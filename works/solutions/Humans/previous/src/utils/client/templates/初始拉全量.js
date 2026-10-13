// GET /api/world/state 返回
{
    timeOfDay: 'day',
    weather: 'clear',
    intensity: 0,
    items: {
        shell_1: { icon: '🐚', x: 550, y: 560 },
        coral_1: { icon: '🪸', x: 533, y: 623 },
        berry_1: { icon: '🫐', x: 443, y: 624 }
    },
    trees: {
        tree_1: { x: 120, y: 180, status: 'alive' },
        tree_2: { x: 350, y: 420, status: 'alive' }
    },
    buildings: {
        shelter_1: { icon: '🏠', x: 180, y: 310 }
    },
    characters: {
        robinson: {
            id: 'robinson',
            name: '鲁滨逊',
            icon: '🧒',
            x: 200,
            y: 320,
            z: 0,
            health: 85,
            energy: 70,
            mood: 60,
            hunger: 50
        },
        father: {
            id: 'father',
            name: '父亲',
            icon: '👨‍🦱',
            x: 260,
            y: 290,
            z: 0,
            health: 80,
            energy: 65,
            mood: 55,
            hunger: 60
        }
    }
}