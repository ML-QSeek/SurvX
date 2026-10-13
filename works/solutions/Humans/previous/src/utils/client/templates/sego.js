// ============================================================
// 👤 人物配置文件
// 角色名称、初始坐标、初始状态等
// ============================================================

const SEGO_CONFIG = {
    // 角色列表
    characters: {
        robinson: {
            name: '鲁滨逊',
            icon: '🧒',
            initial: { x: 200, y: 320, z: 0 },
            stats: {
                health: 85,
                energy: 70,
                mood: 60,
                hunger: 50
            }
        },
        father: {
            name: '父亲',
            icon: '👨‍🦱',
            initial: { x: 260, y: 290, z: 0 },
            stats: {
                health: 80,
                energy: 65,
                mood: 55,
                hunger: 60
            }
        }
    },

    // 默认角色（用于快速引用）
    defaultCharacter: 'robinson'
};