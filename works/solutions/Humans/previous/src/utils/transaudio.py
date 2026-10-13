from mido import MidiFile, MidiTrack, Message, MetaMessage

# ==================== 1. 你的音乐数据（纯列表） ====================

# 《小星星》
twinkle_star = [
    [1, 0.5], [1, 0.5], [5, 0.5], [5, 0.5],
    [6, 0.5], [6, 0.5], [5, 1.0],
    [4, 0.5], [4, 0.5], [3, 0.5], [3, 0.5],
    [2, 0.5], [2, 0.5], [1, 1.0],
    
    [5, 0.5], [5, 0.5], [4, 0.5], [4, 0.5],
    [3, 0.5], [3, 0.5], [2, 1.0],
    [5, 0.5], [5, 0.5], [4, 0.5], [4, 0.5],
    [3, 0.5], [3, 0.5], [2, 1.0],
    
    [1, 0.5], [1, 0.5], [5, 0.5], [5, 0.5],
    [6, 0.5], [6, 0.5], [5, 1.0],
    [4, 0.5], [4, 0.5], [3, 0.5], [3, 0.5],
    [2, 0.5], [2, 0.5], [1, 1.0],
]

# 《欢乐颂》片段
ode_to_joy = [
    [3, 0.5], [3, 0.5], [4, 0.5], [5, 0.5],
    [5, 0.5], [4, 0.5], [3, 0.5], [2, 0.5],
    [1, 0.5], [1, 0.5], [2, 0.5], [3, 0.5],
    [3, 1.0], [2, 0.5], [2, 1.0],
    
    [3, 0.5], [3, 0.5], [4, 0.5], [5, 0.5],
    [5, 0.5], [4, 0.5], [3, 0.5], [2, 0.5],
    [1, 0.5], [1, 0.5], [2, 0.5], [3, 0.5],
    [2, 1.0], [1, 0.5], [1, 1.0],
]


# ==================== 2. 转换器（修正版） ====================

def create_midi(melody, filename="output.mid", tempo=120, 
                ticks_per_beat=480, base_octave=4, instrument=0):
    """
    将纯列表格式的旋律转换成 MIDI 文件。
    
    参数:
        melody       : 列表，格式 [[简谱数字, 拍数, 音量?], ...]
        filename     : 输出文件名
        tempo        : 速度 BPM
        ticks_per_beat: 精度
        base_octave  : 基准八度（简谱 1 对应的八度）
        instrument   : 乐器编号（0=钢琴, 24=尼龙吉他, 73=长笛...）
    """
    mid = MidiFile(ticks_per_beat=ticks_per_beat)
    track = MidiTrack()
    mid.tracks.append(track)
    
    # 设置速度（使用 MetaMessage）
    track.append(MetaMessage('set_tempo', tempo=60000000 // tempo, time=0))
    
    # 选择乐器
    track.append(Message('program_change', program=instrument, time=0))
    
    # 简谱数字 → MIDI 半音偏移映射（C大调，1=C）
    scale_to_semitones = {
        1: 0, 2: 2, 3: 4, 4: 5, 5: 7, 6: 9, 7: 11
    }
    
    for note_data in melody:
        note_num = note_data[0]
        duration_beats = note_data[1]
        velocity = note_data[2] if len(note_data) >= 3 else 80  # 默认音量
        
        # 时值转 ticks
        duration_ticks = int(duration_beats * ticks_per_beat)
        
        if note_num == 0:
            # 休止符：插入空白时间
            track.append(Message('note_off', note=0, velocity=0, time=duration_ticks))
        else:
            # 计算 MIDI 音高：C4=60
            midi_note = 60 + scale_to_semitones[note_num] + (base_octave - 4) * 12
            
            track.append(Message('note_on', note=midi_note, velocity=velocity, time=0))
            track.append(Message('note_off', note=midi_note, velocity=0, time=duration_ticks))
    
    mid.save(filename)
    print(f"✅ {filename} 已生成（{len(melody)} 个音符）")


# ==================== 3. 使用示例 ====================

if __name__ == "__main__":
    # 生成《小星星》
    create_midi(twinkle_star, "../data/civilization/art/twinkle_star.mid")
    
    # 生成《欢乐颂》，速度慢一点，用尼龙弦吉他
    create_midi(ode_to_joy, "../data/civilization/art/ode_to_joy.mid", tempo=100, instrument=24)