import json
import math
import numpy as np
import nlmpy
from scipy.ndimage import gaussian_filter
from skimage import measure
import sys
import argparse
import os
from datetime import datetime
import random

# ============================================================
# 参数解析
# ============================================================
def parse_args():
    parser = argparse.ArgumentParser(description='随机生成岛屿或城市地图配置')
    parser.add_argument('--type', '-t', 
                        choices=['island', 'city'], 
                        default='island',
                        help='地图类型: island(岛屿) 或 city(城市)')
    parser.add_argument('--size', '-s', 
                        choices=['small', 'medium', 'large'], 
                        default='small',
                        help='地图规模: small(小), medium(中), large(大)')
    parser.add_argument('--seed', '-seed', 
                        type=int, 
                        default=None,
                        help='随机种子，用于复现相同地图')
    parser.add_argument('--name', '-n', 
                        type=str, 
                        default=None,
                        help='地图名称（field.name）')
    parser.add_argument('--output', '-o', 
                        type=str, 
                        default=None,
                        help='输出文件名（不含扩展名，自动添加.js）')
    return parser.parse_args()

# ============================================================
# 规模配置
# ============================================================
def get_size_config(size_type):
    configs = {
        'small': {
            'width': 1200,
            'height': 900,
            'scale': 0.06,
            'octaves': 8,
            'island_radius': 0.6,
            'city_radius': 0.5,
            'building_density': 0.5,
            'road_spacing': 40,
            'poi_multiplier': 0.7,
            'label': '小型',
            'item_multiplier': 0.6,
            'species_variety': 0.5,
            'vehicle_density': 0.5,
            'z_min': -60,
            'z_max': 150,
            'name': '小岛',
            'city_name': '小城',
        },
        'medium': {
            'width': 2000,
            'height': 1600,
            'scale': 0.04,
            'octaves': 10,
            'island_radius': 0.65,
            'city_radius': 0.55,
            'building_density': 0.6,
            'road_spacing': 50,
            'poi_multiplier': 1.0,
            'label': '中型',
            'item_multiplier': 1.0,
            'species_variety': 0.7,
            'vehicle_density': 0.7,
            'z_min': -80,
            'z_max': 180,
            'name': '中型岛',
            'city_name': '城市',
        },
        'large': {
            'width': 3000,
            'height': 2400,
            'scale': 0.025,
            'octaves': 12,
            'island_radius': 0.7,
            'city_radius': 0.6,
            'building_density': 0.7,
            'road_spacing': 60,
            'poi_multiplier': 1.5,
            'label': '大型',
            'item_multiplier': 1.5,
            'species_variety': 1.0,
            'vehicle_density': 1.0,
            'z_min': -100,
            'z_max': 200,
            'name': '大型岛',
            'city_name': '大都会',
        }
    }
    return configs.get(size_type, configs['small'])

# ============================================================
# ==================== 岛屿部分 ====================
# ============================================================

ALL_SPECIES = {
    'plants': {
        'beach': [
            {'id': 'coconut_palm', 'icon': '🌴', 'name': '椰子树'},
            {'id': 'beach_grass', 'icon': '🌾', 'name': '海滩草'},
            {'id': 'sea_grape', 'icon': '🍇', 'name': '海葡萄'},
            {'id': 'pandanus', 'icon': '🌿', 'name': '露兜树'},
        ],
        'grassland': [
            {'id': 'wild_berry', 'icon': '🫐', 'name': '野莓'},
            {'id': 'medicinal_herb', 'icon': '🌿', 'name': '药草'},
            {'id': 'wild_flower', 'icon': '🌸', 'name': '野花'},
            {'id': 'clover', 'icon': '🍀', 'name': '三叶草'},
            {'id': 'sunflower', 'icon': '🌻', 'name': '向日葵'},
            {'id': 'lavender', 'icon': '💜', 'name': '薰衣草'},
        ],
        'forest': [
            {'id': 'oak', 'icon': '🌳', 'name': '橡树'},
            {'id': 'pine', 'icon': '🌲', 'name': '松树'},
            {'id': 'mushroom', 'icon': '🍄', 'name': '蘑菇'},
            {'id': 'fern', 'icon': '🌿', 'name': '蕨类'},
            {'id': 'wild_berry_bush', 'icon': '🫐', 'name': '野生浆果丛'},
            {'id': 'moss', 'icon': '🌱', 'name': '苔藓'},
            {'id': 'bamboo', 'icon': '🎋', 'name': '竹子'},
        ],
        'hills': [
            {'id': 'mountain_flower', 'icon': '🏵️', 'name': '山花'},
            {'id': 'wild_thyme', 'icon': '🌿', 'name': '野生百里香'},
            {'id': 'alpine_rose', 'icon': '🌹', 'name': '高山玫瑰'},
        ],
        'mountain': [
            {'id': 'edelweiss', 'icon': '❄️', 'name': '雪绒花'},
            {'id': 'mountain_herb', 'icon': '🌿', 'name': '高山草药'},
            {'id': 'lichen', 'icon': '🪨', 'name': '地衣'},
        ],
        'snow': [
            {'id': 'snow_flower', 'icon': '🏔️', 'name': '雪莲'},
            {'id': 'ice_moss', 'icon': '❄️', 'name': '冰苔'},
            {'id': 'frost_herb', 'icon': '🌨️', 'name': '霜草'},
        ]
    },
    'minerals': {
        'beach': [
            {'id': 'shell', 'icon': '🐚', 'name': '贝壳'},
            {'id': 'driftwood', 'icon': '🪵', 'name': '浮木'},
            {'id': 'sea_glass', 'icon': '🪞', 'name': '海玻璃'},
            {'id': 'sand_dollar', 'icon': '🪙', 'name': '沙钱'},
        ],
        'grassland': [
            {'id': 'flint', 'icon': '🪨', 'name': '燧石'},
            {'id': 'clay', 'icon': '🟤', 'name': '黏土'},
        ],
        'forest': [
            {'id': 'fallen_log', 'icon': '🪵', 'name': '倒木'},
            {'id': 'resin', 'icon': '💧', 'name': '树脂'},
        ],
        'hills': [
            {'id': 'stone', 'icon': '🪨', 'name': '山石'},
            {'id': 'iron_ore', 'icon': '⛏️', 'name': '铁矿'},
            {'id': 'copper_ore', 'icon': '🔶', 'name': '铜矿'},
            {'id': 'quartz', 'icon': '💎', 'name': '石英'},
            {'id': 'granite', 'icon': '🪨', 'name': '花岗岩'},
        ],
        'mountain': [
            {'id': 'gold_ore', 'icon': '✨', 'name': '金矿'},
            {'id': 'diamond', 'icon': '💠', 'name': '钻石'},
            {'id': 'silver_ore', 'icon': '🔘', 'name': '银矿'},
            {'id': 'crystal', 'icon': '💎', 'name': '水晶'},
            {'id': 'obsidian', 'icon': '🪨', 'name': '黑曜石'},
        ],
        'snow': [
            {'id': 'ice_crystal', 'icon': '❄️', 'name': '冰晶'},
            {'id': 'frost_rock', 'icon': '🧊', 'name': '霜岩'},
        ]
    },
    'animals': {
        'beach': [
            {'id': 'crab', 'icon': '🦀', 'name': '螃蟹'},
            {'id': 'starfish', 'icon': '⭐', 'name': '海星'},
            {'id': 'seagull', 'icon': '🕊️', 'name': '海鸥'},
            {'id': 'pelican', 'icon': '🦢', 'name': '鹈鹕'},
            {'id': 'sea_turtle', 'icon': '🐢', 'name': '海龟'},
        ],
        'grassland': [
            {'id': 'butterfly', 'icon': '🦋', 'name': '蝴蝶'},
            {'id': 'rabbit', 'icon': '🐇', 'name': '兔子'},
            {'id': 'fox', 'icon': '🦊', 'name': '狐狸'},
            {'id': 'deer', 'icon': '🦌', 'name': '鹿'},
            {'id': 'badger', 'icon': '🦡', 'name': '獾'},
            {'id': 'owl', 'icon': '🦉', 'name': '猫头鹰'},
        ],
        'forest': [
            {'id': 'squirrel', 'icon': '🐿️', 'name': '松鼠'},
            {'id': 'woodpecker', 'icon': '🐦', 'name': '啄木鸟'},
            {'id': 'wild_boar', 'icon': '🐗', 'name': '野猪'},
            {'id': 'wolf', 'icon': '🐺', 'name': '狼'},
            {'id': 'bear', 'icon': '🐻', 'name': '熊'},
            {'id': 'eagle', 'icon': '🦅', 'name': '鹰'},
            {'id': 'monkey', 'icon': '🐒', 'name': '猴子'},
            {'id': 'snake', 'icon': '🐍', 'name': '蛇'},
        ],
        'hills': [
            {'id': 'mountain_goat', 'icon': '🐐', 'name': '山羊'},
            {'id': 'eagle', 'icon': '🦅', 'name': '金雕'},
            {'id': 'marmot', 'icon': '🐿️', 'name': '旱獭'},
            {'id': 'snow_leopard', 'icon': '🐆', 'name': '雪豹'},
        ],
        'mountain': [
            {'id': 'ibex', 'icon': '🐏', 'name': '野山羊'},
            {'id': 'condor', 'icon': '🦅', 'name': '神鹰'},
            {'id': 'mountain_hare', 'icon': '🐇', 'name': '山兔'},
        ],
        'snow': [
            {'id': 'arctic_fox', 'icon': '🦊', 'name': '北极狐'},
            {'id': 'snow_owl', 'icon': '🦉', 'name': '雪鸮'},
            {'id': 'penguin', 'icon': '🐧', 'name': '企鹅'},
        ]
    }
}

# ============================================================
# 生成岛屿地形
# ============================================================
def generate_island_terrain(width, height, config, seed=None):
    print(f"🏝️ 正在生成{config['label']}岛屿...")
    
    if seed is not None:
        np.random.seed(seed)
        random.seed(seed)
    
    try:
        if hasattr(nlmpy, 'nl'):
            terrain = nlmpy.nl(width, height, scale=config['scale'], octaves=config['octaves'], seed=seed if seed else 42)
        else:
            terrain = nlmpy.noise(width, height, scale=config['scale'], octaves=config['octaves'], seed=seed if seed else 42)
    except:
        x = np.linspace(0, 6, width)
        y = np.linspace(0, 6, height)
        X, Y = np.meshgrid(x, y)
        terrain = np.zeros((height, width))
        for i in range(config['octaves']):
            freq = 1.5 ** i
            amp = 1.0 / (freq * 1.3)
            terrain += amp * (np.sin(freq * X * np.pi) * np.cos(freq * Y * np.pi))
        terrain = (terrain - np.min(terrain)) / (np.max(terrain) - np.min(terrain))
    
    terrain = (terrain - np.min(terrain)) / (np.max(terrain) - np.min(terrain))
    
    x = np.linspace(-1.6, 1.6, width)
    y = np.linspace(-1.6, 1.6, height)
    X, Y = np.meshgrid(x, y)
    
    base_radius = np.sqrt(X*X + Y*Y)
    island_mask = 1 - base_radius * config['island_radius']
    
    np.random.seed(seed if seed else 42)
    noise1 = 0.12 * np.sin(X * 8 + 1.7 + np.random.rand() * 2) * np.cos(Y * 6 + 0.8 + np.random.rand() * 2)
    noise2 = 0.08 * np.sin(X * 15 + 2.3 + np.random.rand() * 2) * np.cos(Y * 12 + 1.1 + np.random.rand() * 2)
    noise3 = 0.06 * np.sin((X + Y) * 20 + 0.5 + np.random.rand() * 2)
    noise4 = 0.05 * np.cos(X * 25 - Y * 18 + 0.3 + np.random.rand() * 2) * np.sin(X * 10 + Y * 8 + np.random.rand() * 2)
    bay_effect = 0.1 * np.sin(X * 3 + np.random.rand() * 2) * np.cos(Y * 4 + np.random.rand() * 2) * (1 - base_radius * 0.5)
    
    island_mask = island_mask + noise1 + noise2 + noise3 + noise4 + bay_effect
    island_mask = np.clip(island_mask, 0, 1)
    island_mask = gaussian_filter(island_mask, sigma=0.8)
    
    terrain = terrain * island_mask
    terrain = terrain / (np.max(terrain) + 0.001)
    
    height_map = terrain * (config['z_max'] - config['z_min']) + config['z_min']
    edge_slope = np.clip((island_mask * 1.2) ** 0.7, 0, 1)
    height_map = height_map * edge_slope
    height_map = gaussian_filter(height_map, sigma=1.2)
    
    detail_noise = np.random.randn(height, width) * 0.5
    detail_noise = gaussian_filter(detail_noise, sigma=2.5)
    height_map = height_map + detail_noise * 0.3
    height_map[island_mask < 0.01] = config['z_min']
    
    print(f"   ✅ 岛屿生成完成 (最高点: {np.max(height_map):.1f}m)")
    return height_map, island_mask

# ============================================================
# 提取地形区域
# ============================================================
def extract_terrain_regions(height_map, island_mask, config, seed=None):
    if seed is not None:
        random.seed(seed)
    
    terrain_layers = [
        {"id": "beach", "name": "🏖️ 海滩", "color": "#f4d03f", "z_min": -5, "z_max": 5},
        {"id": "grassland", "name": "🌿 草地", "color": "#7cb342", "z_min": 5, "z_max": 20},
        {"id": "forest", "name": "🌳 森林", "color": "#2e7d32", "z_min": 20, "z_max": 50},
        {"id": "hills", "name": "⛰️ 丘陵", "color": "#8d6e63", "z_min": 50, "z_max": 80},
        {"id": "mountain", "name": "🏔️ 高山", "color": "#a569bd", "z_min": 80, "z_max": 120},
        {"id": "snow", "name": "❄️ 雪顶", "color": "#ffffff", "z_min": 120, "z_max": 250},
    ]
    
    terrains = []
    
    for layer in terrain_layers:
        mask = (height_map >= layer['z_min']) & (height_map <= layer['z_max']) & (island_mask > 0.01)
        
        if np.sum(mask) < 500:
            continue
        
        try:
            contours = measure.find_contours(mask, 0.5)
            if not contours:
                continue
            
            contour = max(contours, key=len)
            if len(contour) < 15:
                continue
            
            if len(contour) > 60:
                step = max(1, len(contour) // 50)
                contour = contour[::step]
            
            points = []
            for pt in contour:
                y, x = int(pt[0]), int(pt[1])
                if 0 <= y < height_map.shape[0] and 0 <= x < height_map.shape[1]:
                    z = round(float(height_map[y, x]), 1)
                    points.append({"x": float(x), "y": float(y), "z": z})
            
            if len(points) < 5:
                continue
            
            if points[0]['x'] != points[-1]['x'] or points[0]['y'] != points[-1]['y']:
                points.append(points[0].copy())
            
            terrains.append({
                "id": layer['id'],
                "name": layer['name'],
                "color": layer['color'],
                "points": points
            })
            
        except Exception as e:
            continue
    
    terrains.sort(key=lambda t: sum(p['z'] for p in t['points']) / len(t['points']))
    
    return terrains

# ============================================================
# 生成岛屿物品
# ============================================================
def generate_island_items(height_map, terrains, config, seed=None):
    print("\n🎲 正在生成岛屿生物和资源...")
    
    if seed is not None:
        np.random.seed(seed)
        random.seed(seed)
    
    items = []
    
    variety_ratio = config['species_variety']
    quantity_multiplier = config['item_multiplier']
    
    terrain_item_map = {
        'beach': 'beach', 'grassland': 'grassland', 'forest': 'forest',
        'hills': 'hills', 'mountain': 'mountain', 'snow': 'snow',
    }
    
    total_area = sum(len(t.get('points', [])) for t in terrains)
    if total_area == 0:
        return items
    
    for terrain in terrains:
        terrain_id = terrain['id']
        item_category = terrain_item_map.get(terrain_id)
        
        if not item_category:
            continue
        
        available_species = []
        if item_category in ALL_SPECIES['plants']:
            available_species.extend(ALL_SPECIES['plants'][item_category])
        if item_category in ALL_SPECIES['minerals']:
            available_species.extend(ALL_SPECIES['minerals'][item_category])
        if item_category in ALL_SPECIES['animals']:
            available_species.extend(ALL_SPECIES['animals'][item_category])
        
        if not available_species:
            continue
        
        terrain_points = terrain.get('points', [])
        if len(terrain_points) < 10:
            continue
        
        area_ratio = len(terrain_points) / total_area
        
        if config['label'] == '小型':
            species_count = max(3, int(len(available_species) * 0.5 * variety_ratio))
            base_qty = max(2, int(8 * area_ratio * quantity_multiplier))
        elif config['label'] == '中型':
            species_count = max(5, int(len(available_species) * 0.7 * variety_ratio))
            base_qty = max(3, int(12 * area_ratio * quantity_multiplier))
        else:
            species_count = max(7, int(len(available_species) * 0.9 * variety_ratio))
            base_qty = max(4, int(18 * area_ratio * quantity_multiplier))
        
        species_count = min(species_count, len(available_species))
        selected_species = random.sample(available_species, species_count)
        
        print(f"   🌍 {terrain['name']}: {len(selected_species)} 种, ~{base_qty * len(selected_species)} 个")
        
        for species in selected_species:
            quantity = max(1, int(base_qty * random.uniform(0.7, 1.3)))
            
            for _ in range(quantity):
                base_pt = random.choice(terrain_points[:-1])
                x = base_pt['x'] + random.randint(-25, 25)
                y = base_pt['y'] + random.randint(-25, 25)
                z = base_pt['z'] + random.uniform(-3, 3)
                
                x = max(0, min(config['width'] - 1, x))
                y = max(0, min(config['height'] - 1, y))
                
                items.append({
                    "id": species['id'],
                    "icon": species['icon'],
                    "name": species['name'],
                    "x": round(x, 1),
                    "y": round(y, 1),
                    "z": round(z, 1)
                })
    
    print(f"   ✅ 总共生成 {len(items)} 个物品/生物")
    return items

# ============================================================
# ==================== 城市部分 ====================
# ============================================================

def generate_city_terrain(width, height, config, seed=None):
    print(f"🏙️ 正在生成{config['label']}城市...")
    
    if seed is not None:
        np.random.seed(seed)
        random.seed(seed)
    
    x = np.linspace(-1.5, 1.5, width)
    y = np.linspace(-1.5, 1.5, height)
    X, Y = np.meshgrid(x, y)
    
    terrain = 1 - np.sqrt(X*X + Y*Y) * 0.3
    terrain = np.clip(terrain, 0, 1)
    terrain += 0.05 * np.sin(X * 8 + np.random.rand() * 2) * np.cos(Y * 6 + np.random.rand() * 2)
    terrain += 0.03 * np.sin(X * 15 + Y * 10 + np.random.rand() * 2)
    terrain = np.clip(terrain, 0, 1)
    terrain = gaussian_filter(terrain, sigma=0.5)
    
    city_mask = 1 - np.sqrt(X*X + Y*Y) * config['city_radius']
    city_mask = np.clip(city_mask, 0, 1)
    city_mask = gaussian_filter(city_mask, sigma=0.3)
    
    terrain = terrain * city_mask
    terrain = terrain / (np.max(terrain) + 0.001)
    height_map = terrain * 30
    height_map = gaussian_filter(height_map, sigma=0.8)
    
    print(f"   ✅ 城市地形生成完成")
    return height_map, city_mask

def generate_city_features(width, height, city_mask, config, seed=None):
    print("\n🏢 正在生成城市要素...")
    
    if seed is not None:
        np.random.seed(seed)
        random.seed(seed)
    
    center_x, center_y = width // 2, height // 2
    terrains = []
    items = []
    
    # 功能区定义
    zones = [
        {"id": "downtown", "name": "🏢 市中心", "color": "#34495e", "cx": center_x, "cy": center_y, "radius": int(200 * config['poi_multiplier'])},
        {"id": "residential_1", "name": "🏘️ 住宅区A", "color": "#27ae60", "cx": center_x + int(300 * config['poi_multiplier']), "cy": center_y - int(200 * config['poi_multiplier']), "radius": int(180 * config['poi_multiplier'])},
        {"id": "residential_2", "name": "🏘️ 住宅区B", "color": "#27ae60", "cx": center_x - int(300 * config['poi_multiplier']), "cy": center_y - int(200 * config['poi_multiplier']), "radius": int(160 * config['poi_multiplier'])},
        {"id": "residential_3", "name": "🏘️ 住宅区C", "color": "#27ae60", "cx": center_x + int(250 * config['poi_multiplier']), "cy": center_y + int(250 * config['poi_multiplier']), "radius": int(150 * config['poi_multiplier'])},
        {"id": "park", "name": "🌳 公园", "color": "#2ecc71", "cx": center_x - int(100 * config['poi_multiplier']), "cy": center_y + int(100 * config['poi_multiplier']), "radius": int(150 * config['poi_multiplier'])},
        {"id": "commercial_1", "name": "🛍️ 商业区A", "color": "#e67e22", "cx": center_x + int(400 * config['poi_multiplier']), "cy": center_y - int(50 * config['poi_multiplier']), "radius": int(120 * config['poi_multiplier'])},
        {"id": "commercial_2", "name": "🛍️ 商业区B", "color": "#e67e22", "cx": center_x - int(380 * config['poi_multiplier']), "cy": center_y + int(50 * config['poi_multiplier']), "radius": int(110 * config['poi_multiplier'])},
    ]
    
    if config['label'] == '大型':
        zones.append({"id": "waterfront", "name": "🌊 滨水区", "color": "#3498db", "cx": center_x + int(450 * config['poi_multiplier']), "cy": center_y + int(150 * config['poi_multiplier']), "radius": int(100 * config['poi_multiplier'])})
        zones.append({"id": "industrial", "name": "🏭 工业区", "color": "#7f8c8d", "cx": center_x + int(50 * config['poi_multiplier']), "cy": center_y + int(450 * config['poi_multiplier']), "radius": int(140 * config['poi_multiplier'])})
    
    # 生成环形道路
    ring_roads = [
        {"name": "🛣️ 一环", "color": "#e74c3c", "ratio": 0.15},
        {"name": "🛣️ 二环", "color": "#e67e22", "ratio": 0.30},
        {"name": "🛣️ 三环", "color": "#f1c40f", "ratio": 0.45},
    ]
    if config['label'] in ['大型', '中型']:
        ring_roads.append({"name": "🛣️ 四环", "color": "#2ecc71", "ratio": 0.55})
    
    for ring in ring_roads:
        radius = ring["ratio"] * min(width, height) * 0.5
        points = []
        num_points = max(60, int(radius * 0.5))
        for i in range(num_points + 1):
            angle = (i / num_points) * 2 * math.pi
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            if 0 <= int(y) < height and 0 <= int(x) < width:
                if city_mask[int(y), int(x)] > 0.1:
                    points.append({"x": round(x, 1), "y": round(y, 1), "z": 0.5})
        if len(points) > 10:
            terrains.append({"id": f"ring_road_{ring['name']}", "name": ring['name'], "color": ring['color'], "points": points})
    
    # 生成放射状道路
    num_radial = max(6, min(12, int(8 * config['poi_multiplier'])))
    for i in range(num_radial):
        angle = (i / num_radial) * 2 * math.pi + random.uniform(-0.05, 0.05)
        points = []
        for dist in range(0, int(min(width, height) * 0.5), 8):
            x = center_x + dist * math.cos(angle)
            y = center_y + dist * math.sin(angle)
            if 0 <= int(y) < height and 0 <= int(x) < width:
                if city_mask[int(y), int(x)] > 0.05:
                    points.append({"x": round(x, 1), "y": round(y, 1), "z": 0.5})
                else:
                    break
        if len(points) > 20:
            terrains.append({"id": f"radial_road_{i}", "name": f"🛣️ 放射路{i+1}", "color": "#3498db", "points": points})
    
    # 生成功能区和建筑
    for zone in zones:
        cx, cy, radius = zone['cx'], zone['cy'], zone['radius']
        
        # 区域轮廓
        zone_points = []
        num_pts = 30
        for i in range(num_pts + 1):
            angle = (i / num_pts) * 2 * math.pi
            r = radius * (0.85 + 0.15 * math.sin(angle * 3 + 1.2) * math.cos(angle * 2 + 0.7))
            px = cx + r * math.cos(angle)
            py = cy + r * math.sin(angle)
            if 0 <= int(py) < height and 0 <= int(px) < width:
                zone_points.append({"x": round(px, 1), "y": round(py, 1), "z": 0.5})
        
        if len(zone_points) > 5:
            terrains.append({"id": f"zone_{zone['id']}", "name": zone['name'], "color": zone['color'], "points": zone_points})
        
        # 建筑
        if zone['id'] != 'park':
            num_buildings = int(radius * radius * config['building_density'] / 2000)
            num_buildings = max(10, min(60, num_buildings))
            
            for _ in range(num_buildings):
                angle = random.uniform(0, 2 * math.pi)
                dist = random.uniform(0, radius * 0.85)
                bx = cx + dist * math.cos(angle)
                by = cy + dist * math.sin(angle)
                
                if 0 <= int(by) < height and 0 <= int(bx) < width:
                    if city_mask[int(by), int(bx)] > 0.1:
                        items.append({
                            "id": f"building_{zone['id']}_{len(items)}",
                            "icon": "🏢",
                            "name": zone['name'].replace('🏢 ', '').replace('🏘️ ', '').replace('🛍️ ', '').replace('🏭 ', ''),
                            "x": round(bx, 1),
                            "y": round(by, 1),
                            "z": 0.5
                        })
    
    # 生成POI
    poi_types = [
        {"icon": "🍺", "name": "酒吧", "count": int(5 * config['poi_multiplier'])},
        {"icon": "🍽️", "name": "餐厅", "count": int(8 * config['poi_multiplier'])},
        {"icon": "☕", "name": "咖啡馆", "count": int(6 * config['poi_multiplier'])},
        {"icon": "🏥", "name": "医院", "count": max(1, int(2 * config['poi_multiplier']))},
        {"icon": "🏫", "name": "学校", "count": max(1, int(3 * config['poi_multiplier']))},
        {"icon": "🛒", "name": "超市", "count": int(3 * config['poi_multiplier'])},
        {"icon": "💪", "name": "健身房", "count": int(2 * config['poi_multiplier'])},
        {"icon": "🏨", "name": "酒店", "count": int(2 * config['poi_multiplier'])},
        {"icon": "⛪", "name": "教堂", "count": 1},
        {"icon": "🏛️", "name": "博物馆", "count": 1},
    ]
    
    if config['label'] == '大型':
        poi_types.extend([
            {"icon": "🎬", "name": "电影院", "count": 2},
            {"icon": "📚", "name": "图书馆", "count": 1},
        ])
    
    for poi in poi_types:
        for _ in range(poi['count']):
            for attempt in range(50):
                px = random.uniform(center_x - min(width, height) * 0.45, center_x + min(width, height) * 0.45)
                py = random.uniform(center_y - min(width, height) * 0.45, center_y + min(width, height) * 0.45)
                if 0 <= int(py) < height and 0 <= int(px) < width:
                    if city_mask[int(py), int(px)] > 0.2:
                        items.append({
                            "id": f"poi_{poi['name']}_{len(items)}",
                            "icon": poi['icon'],
                            "name": poi['name'],
                            "x": round(px, 1),
                            "y": round(py, 1),
                            "z": 0.5
                        })
                        break
    
    # 生成车辆
    vehicle_types = [
        {'icon': '🚗', 'name': '汽车'},
        {'icon': '🚌', 'name': '公交车'},
        {'icon': '🚛', 'name': '卡车'},
        {'icon': '🚕', 'name': '出租车'},
        {'icon': '🏍️', 'name': '摩托车'},
        {'icon': '🚲', 'name': '自行车'},
        {'icon': '🛵', 'name': '踏板车'},
    ]
    
    num_vehicles = int(20 * config['vehicle_density'] * config['poi_multiplier'])
    num_vehicles = max(5, min(80, num_vehicles))
    
    for _ in range(num_vehicles):
        vehicle = random.choice(vehicle_types)
        for attempt in range(50):
            vx = random.uniform(center_x - min(width, height) * 0.4, center_x + min(width, height) * 0.4)
            vy = random.uniform(center_y - min(width, height) * 0.4, center_y + min(width, height) * 0.4)
            if 0 <= int(vy) < height and 0 <= int(vx) < width:
                if city_mask[int(vy), int(vx)] > 0.1:
                    items.append({
                        "id": f"vehicle_{vehicle['name']}_{len(items)}",
                        "icon": vehicle['icon'],
                        "name": vehicle['name'],
                        "x": round(vx, 1),
                        "y": round(vy, 1),
                        "z": 0.5
                    })
                    break
    
    # 城市边界
    boundary_points = []
    for i in range(60):
        angle = (i / 60) * 2 * math.pi
        radius = min(width, height) * 0.48
        px = center_x + radius * math.cos(angle)
        py = center_y + radius * math.sin(angle)
        boundary_points.append({"x": round(px, 1), "y": round(py, 1), "z": 0.5})
    boundary_points.append(boundary_points[0].copy())
    
    terrains.append({"id": "city_boundary", "name": "🏙️ 城市边界", "color": "#2c3e50", "points": boundary_points})
    
    print(f"   ✅ 生成了 {len(terrains)} 个区域/道路, {len(items)} 个要素")
    return terrains, items

# ============================================================
# ==================== 主函数 ====================
# ============================================================
def main():
    args = parse_args()
    
    config = get_size_config(args.size)
    
    # 设置地图名称
    map_name = args.name if args.name else (config['name'] if args.type == 'island' else config['city_name'])
    
    if args.output:
        filename = args.output
        if not filename.endswith('.js'):
            filename += '.js'
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{args.type}_{args.size}_{timestamp}.js"
    
    print("=" * 60)
    print(f"🎯 生成地图配置: {args.type} ({args.size} - {config['label']})")
    print(f"📝 地图名称: {map_name}")
    print(f"📐 尺寸: {config['width']} x {config['height']}")
    print(f"🔢 随机种子: {args.seed if args.seed else '随机'}")
    print(f"📄 输出文件: {filename}")
    print("=" * 60)
    
    if args.type == 'island':
        height_map, island_mask = generate_island_terrain(
            config['width'], config['height'], config, args.seed
        )
        
        print("\n正在提取地形区域...")
        terrains = extract_terrain_regions(height_map, island_mask, config, args.seed)
        print(f"✅ 提取了 {len(terrains)} 个地形区域")
        
        items = generate_island_items(height_map, terrains, config, args.seed)
        
    else:  # city
        height_map, city_mask = generate_city_terrain(
            config['width'], config['height'], config, args.seed
        )
        
        terrains, items = generate_city_features(
            config['width'], config['height'], city_mask, config, args.seed
        )
    
    # 构建输出
    field_config = {
        "field": {
            "name": map_name,
            "width": config['width'],
            "height": config['height'],
            "zMin": config['z_min'],
            "zMax": config['z_max']
        },
        "terrains": terrains,
        "items": items
    }
    
    # 写入文件
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("const FIELD_CONFIG = ")
        json.dump(field_config, f, indent=2, ensure_ascii=False)
        f.write(";\n")
    
    print("\n" + "=" * 60)
    print(f"✅ 已导出: {filename}")
    print(f"📊 统计:")
    print(f"   - 地形/区域: {len(terrains)} 个")
    for t in terrains:
        print(f"     {t['name']}: {len(t['points'])} 个顶点")
    print(f"   - 物品/要素: {len(items)} 个")
    print("=" * 60)
    print(f"\n文件格式: const FIELD_CONFIG = {{ ... }};")

if __name__ == "__main__":
    main()