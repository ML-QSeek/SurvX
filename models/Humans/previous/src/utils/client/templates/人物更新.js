// 1. 移动位置
socket.emit('update', {
    type: 'character',
    data: {
        id: 'robinson',
        x: 250,
        y: 340
    }
});

// 2. 状态变化 + 说话
socket.emit('update', {
    type: 'character',
    data: {
        id: 'robinson',
        health: 75,
        energy: 60,
        speech: '🗣️ 好累啊...'
    }
});

// 3. 全部一起
socket.emit('update', {
    type: 'character',
    data: {
        id: 'robinson',
        x: 300,
        y: 400,
        health: 80,
        thought: '💭 前面有片森林'
    }
});

// 4. 新人物
socket.emit('update', {
    type: 'character',
    data: {
        id: 'friday',
        name: '星期五',
        icon: '🧑🏿',
        x: 150,
        y: 250,
        z: 0,
        health: 90,
        energy: 80,
        mood: 70,
        hunger: 40
    }
});

// 5. 删除人物
socket.emit('update', {
    type: 'character',
    data: {
        id: 'friday',
        _delete: true
    }
});