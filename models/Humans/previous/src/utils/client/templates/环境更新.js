// 1. 改变天气
socket.emit('update', {
    type: 'world',
    data: {
        weather: 'rain',
        intensity: 0.6
    }
});

// 2. 改变时间 + 天气
socket.emit('update', {
    type: 'world',
    data: {
        timeOfDay: 'night',
        weather: 'storm',
        intensity: 0.8
    }
});

// 3. 新增物品
socket.emit('update', {
    type: 'world',
    data: {
        items: {
            new_shell: { icon: '🐚', x: 520, y: 540 }
        }
    }
});

// 4. 更新物品位置
socket.emit('update', {
    type: 'world',
    data: {
        items: {
            berry_1: { x: 460, y: 640 }
        }
    }
});

// 5. 删除物品 (推 null)
socket.emit('update', {
    type: 'world',
    data: {
        items: {
            coral_1: null
        }
    }
});

// 6. 多件事一起
socket.emit('update', {
    type: 'world',
    data: {
        timeOfDay: 'dusk',
        items: {
            shell_1: { x: 560, y: 570 },
            berry_1: null
        },
        trees: {
            tree_5: { x: 200, y: 300, status: 'cut' }
        }
    }
});