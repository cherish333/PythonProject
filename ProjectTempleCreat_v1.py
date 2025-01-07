
#完成版的工程创建插件优化版
import sys
import os
import unreal
import tkinter as tk
from tkinter import ttk, messagebox
# 在文件开头定义常量
FRAME_RATE = 30
SEQUENCE_LENGTH = 500
BASE_FOLDERS = ["000COMP", "001Animat", "002Map", "003VFX", "004Light"]
LEVEL_PREFIXES = {
    "001Animat": "Ani_map",
    "002Map": "Sc_Map",
    "003VFX": "Vfx_Map",
    "004Light": "Light_Map"
}
SEQUENCE_PREFIXES = {
    "000COMP": "Main_Sequence",
    "001Animat": "Anim_Sequence", 
    "002Map": "Sc_Sequence",
    "003VFX": "VFX_Sequence",
    "004Light": "Light_Sequence"
}
TRACK_NAMES = {
    "001Animat": "Animation",
    "002Map": "Scene",
    "003VFX": "VFX",
    "004Light": "Lighting"
}
# 添加子文件夹结构常量
SUB_FOLDERS = {
    "001Animat": ["001Setup", "002Animation", "003Ani_Map", "999Ani_Resource"],
    "002Map": ["001Sc_Map", "002Sc_Sequence", "999Sc_Resource"],
    "003VFX": ["001VFX_Map", "002VFX_Sequence", "999VFX_Resource"],
    "004Light": ["001Light_Map", "002Light_Sequence", "999Light_Resource"]
}
# 更新关卡和序列的路径前缀
LEVEL_PATHS = {
    "001Animat": "003Ani_Map",
    "002Map": "001Sc_Map",
    "003VFX": "001VFX_Map",
    "004Light": "001Light_Map"
}
SEQUENCE_PATHS = {
    "001Animat": "003Ani_Map",
    "002Map": "002Sc_Sequence",
    "003VFX": "002VFX_Sequence",
    "004Light": "002Light_Sequence"
}
def create_folder_structure(project_name, shot_count):
    base_path = f"/Game/{project_name}"
    
    # 创建基础文件夹和子文件夹
    for folder in BASE_FOLDERS:
        folder_path = f"{base_path}/{folder}"
        unreal.EditorAssetLibrary.make_directory(folder_path)
        
        # 创建子文件夹
        if folder in SUB_FOLDERS:
            for sub_folder in SUB_FOLDERS[folder]:
                sub_folder_path = f"{folder_path}/{sub_folder}"
                unreal.EditorAssetLibrary.make_directory(sub_folder_path)
    # 修改关卡创建路径
    for shot_num in range(1, shot_count + 1):
        shot_num_str = str(shot_num).zfill(4)
        print(f"\n========== 处理镜头 {shot_num_str} ==========")
        
        # 获取level subsystem
        level_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        
        # 更新子关卡路径
        sublevel_paths = []
        for folder, prefix in LEVEL_PREFIXES.items():
            level_name = f"{prefix}_shot{shot_num_str}"
            level_path = f"{base_path}/{folder}/{LEVEL_PATHS[folder]}/{level_name}"
            sublevel_paths.append(level_path)
            
            if not unreal.EditorAssetLibrary.does_asset_exist(level_path):
                sublevel = level_subsystem.new_level(level_path)
                level_subsystem.save_current_level()
                print(f"创建子关卡: {level_name}")
        
        # 创建主关卡
        main_level_name = f"Map_shot{shot_num_str}_V001"
        main_level_path = f"{base_path}/000COMP/{main_level_name}"
        
        if not unreal.EditorAssetLibrary.does_asset_exist(main_level_path):
            main_level = level_subsystem.new_level(main_level_path)
            level_subsystem.save_current_level()
            print(f"创建主关卡: {main_level_name}")
        
        try:
            # 保存并重新加载
            level_subsystem.save_current_level()
            unreal.EditorLoadingAndSavingUtils.save_dirty_packages(
                save_map_packages=True,
                save_content_packages=True
            )
            
            # 加载主关卡
            unreal.EditorLoadingAndSavingUtils.load_map(main_level_path)
            editor_world = unreal.EditorLevelLibrary.get_editor_world()
            
            if not editor_world:
                continue
            
            # 添加子关卡
            for sublevel_path in reversed(sublevel_paths):
                try:
                    sublevel_asset = unreal.EditorAssetLibrary.load_asset(sublevel_path)
                    if not sublevel_asset:
                        continue
                    
                    # 使用LevelStreamingAlwaysLoaded而不是LevelStreamingDynamic
                    streaming_level = unreal.EditorLevelUtils.add_level_to_world(
                        editor_world,
                        sublevel_path,
                        unreal.LevelStreamingAlwaysLoaded
                    )
                    
                    if streaming_level:
                        streaming_level.set_editor_property('should_be_loaded', True)
                        streaming_level.set_editor_property('should_be_visible', True)
                        print(f"添加子关卡: {sublevel_path.split('/')[-1]}")
                        
                        level_subsystem.save_current_level()
                        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(
                            save_map_packages=True,
                            save_content_packages=True
                        )
                except Exception as e:
                    print(f"添加子关卡出错: {str(e)}")
            
            # 最终保存
            level_subsystem.save_current_level()
            unreal.EditorLoadingAndSavingUtils.save_dirty_packages(
                save_map_packages=True,
                save_content_packages=True
            )
            
        except Exception as e:
            print(f"处理主关卡出错: {str(e)}")
        
        # 创建序列并放置到对应关卡
        sequence_prefixes = {
            "000COMP": "Main_Sequence",
            "001Animat": "Anim_Sequence", 
            "002Map": "Sc_Sequence",
            "003VFX": "VFX_Sequence",
            "004Light": "Light_Sequence"
        }
        
        # 先创建所有序列
        sequences_dict = {}
        
        # 创建摄像机序列（只创建一次）
        cam_sequence_name = f"Sequence_Cam_v001"  # 移除shot编号
        cam_sequence_path = f"{base_path}/000COMP/{cam_sequence_name}"
        
        if not unreal.EditorAssetLibrary.does_asset_exist(cam_sequence_path):
            try:
                asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
                cam_sequence = asset_tools.create_asset(
                    asset_name=cam_sequence_name,
                    package_path=f"{base_path}/000COMP",
                    asset_class=unreal.LevelSequence,
                    factory=unreal.LevelSequenceFactoryNew()
                )
                
                if cam_sequence:
                    # 设置摄像机序列的帧率和时间范围
                    frame_rate = unreal.FrameRate(30, 1)  # 30fps
                    cam_sequence.set_display_rate(frame_rate)
                    cam_sequence.set_playback_end_seconds(500 / 30.0)
                    cam_sequence.set_playback_start_seconds(0)
                    
                    unreal.EditorAssetLibrary.save_asset(cam_sequence_path)
                    print(f"创建摄像机序列: {cam_sequence_name}")
                    sequences_dict["000COMP_CAM"] = cam_sequence
                    
            except Exception as e:
                print(f"创建摄像机序列出错: {str(e)}")
        
        # 创建其他序列
        for folder, prefix in SEQUENCE_PREFIXES.items():
            if folder == "000COMP":
                sequence_path = f"{base_path}/{folder}"
            else:
                sequence_path = f"{base_path}/{folder}/{SEQUENCE_PATHS[folder]}"
            
            sequence_name = f"{prefix}_shot{shot_num_str}"
            full_sequence_path = f"{sequence_path}/{sequence_name}"
            
            try:
                if not unreal.EditorAssetLibrary.does_directory_exist(sequence_path):
                    unreal.EditorAssetLibrary.make_directory(sequence_path)
                
                asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
                new_sequence = asset_tools.create_asset(
                    asset_name=sequence_name,
                    package_path=sequence_path,
                    asset_class=unreal.LevelSequence,
                    factory=unreal.LevelSequenceFactoryNew()
                )
                
                if new_sequence:
                    # 设置序列的帧率和时间范围
                    frame_rate = unreal.FrameRate(30, 1)  # 30fps
                    new_sequence.set_display_rate(frame_rate)
                    new_sequence.set_playback_end_seconds(500 / 30.0)
                    new_sequence.set_playback_start_seconds(0)
                    
                    unreal.EditorAssetLibrary.save_asset(full_sequence_path)
                    print(f"创建序列: {sequence_name}")
                    sequences_dict[folder] = new_sequence
                    
            except Exception as e:
                print(f"创建序列出错: {str(e)}")
        # 在主序列中添加子序列轨道和Shot Track
        if "000COMP" in sequences_dict:
            main_sequence = sequences_dict["000COMP"]
            sub_sequence_folders = ["001Animat", "002Map", "003VFX", "004Light"]
            
            try:
                # 添加Shot Track
                shot_track = main_sequence.add_track(unreal.MovieSceneCinematicShotTrack)
                if shot_track:
                    # 添加Shot部分
                    shot_section = shot_track.add_section()
                    if shot_section:
                        # 设置Shot的范围为0-500
                        shot_section.set_range(0, 500)
                        # 设置Shot的显示名称
                        shot_section.set_shot_display_name(f"Shot_{shot_num_str}")
                        
                        # 加载并设置摄像机序列
                        cam_sequence = unreal.load_asset(cam_sequence_path)
                        if cam_sequence:
                            shot_section.set_sequence(cam_sequence)
                            print(f"添加Shot Track: Shot_{shot_num_str} (with camera sequence)")
                
                # 添加其他子序列轨道
                for folder in sub_sequence_folders:
                    if folder in sequences_dict:
                        # 创建子序列轨道
                        sub_track = main_sequence.add_track(unreal.MovieSceneSubTrack)
                        if sub_track:
                            # 添加序列部分
                            section = sub_track.add_section()
                            if section:
                                # 设置子序列
                                section.set_sequence(sequences_dict[folder])
                                
                                # 设置section范围为0-500
                                section.set_range(0, 500)
                                
                                # 设置轨道名称
                                track_name = {
                                    "001Animat": "Animation",
                                    "002Map": "Scene",
                                    "003VFX": "VFX",
                                    "004Light": "Lighting"
                                }[folder]
                                sub_track.set_display_name(track_name)
                                print(f"添加子序列轨道: {track_name}")
                
                # 保存主序列
                main_sequence_path = f"{base_path}/000COMP/{sequence_prefixes['000COMP']}_shot{shot_num_str}"
                unreal.EditorAssetLibrary.save_asset(main_sequence_path)
                print("保存主序列完成")
                
            except Exception as e:
                print(f"添加子序列轨道出错: {str(e)}")
        
        # 然后将序列放置到对应关卡
        for folder, prefix in sequence_prefixes.items():
            sequence_name = f"{prefix}_shot{shot_num_str}"
            sequence_path = f"{base_path}/{folder}/{sequence_name}"
            
            # 确定目标关卡路径
            level_path = None
            if folder == "000COMP":
                level_path = main_level_path
            else:
                level_prefix = LEVEL_PREFIXES.get(folder)
                if level_prefix:
                    level_path = f"{base_path}/{folder}/{LEVEL_PATHS[folder]}/{level_prefix}_shot{shot_num_str}"
            
            if level_path:
                try:
                    # 加载目标关卡
                    unreal.EditorLoadingAndSavingUtils.load_map(level_path)
                    target_world = unreal.EditorLevelLibrary.get_editor_world()
                    
                    if target_world:
                        # 修改这部分代码，让所有关卡都创建序列Actor
                        sequence_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
                            unreal.LevelSequenceActor,
                            unreal.Vector(0, 0, 0),
                            unreal.Rotator(0, 0, 0)
                        )
                        
                        if sequence_actor:
                            # 设置Actor的名称为序列名称
                            sequence_actor.set_actor_label(sequence_name)
                            
                            loaded_sequence = unreal.load_asset(sequence_path)
                            if loaded_sequence:
                                # 使用正确的方法设置序列
                                sequence_actor.set_sequence(loaded_sequence)
                                print(f"放置序列 {sequence_name} 到关卡 {level_path.split('/')[-1]}")
                        
                        # 如果是动画关卡，额外创建Anim_actor
                        if folder == "001Animat":
                            # 创建空的Actor
                            anim_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
                                unreal.Actor,
                                unreal.Vector(0, 0, 0),
                                unreal.Rotator(0, 0, 0)
                            )
                            
                            if anim_actor:
                                # 设置Actor的名称
                                anim_actor.set_actor_label("Anim_actor")
                                print(f"创建Anim_actor到关卡: {level_path.split('/')[-1]}")
                                
                                # 获取动画序列
                                anim_sequence = sequences_dict.get(folder)
                                if anim_sequence:
                                    # 为Actor创建绑定和轨道
                                    binding = anim_sequence.add_possessable(anim_actor)
                                    if binding:
                                        print(f"将Anim_actor添加到序列: {sequence_name}")
                        # 保存关卡
                        level_subsystem.save_current_level()
                        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(
                            save_map_packages=True,
                            save_content_packages=True
                        )
                except Exception as e:
                    print(f"放置序列出错: {str(e)}")
        
        # 最后重新加载主关卡
        unreal.EditorLoadingAndSavingUtils.load_map(main_level_path)
def create_sequence(name, path, frame_rate=30, length=500):
    """创建序列并设置基本属性"""
    try:
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        sequence = asset_tools.create_asset(
            asset_name=name,
            package_path=path,
            asset_class=unreal.LevelSequence,
            factory=unreal.LevelSequenceFactoryNew()
        )
        
        if sequence:
            frame_rate_obj = unreal.FrameRate(frame_rate, 1)
            sequence.set_display_rate(frame_rate_obj)
            sequence.set_playback_end_seconds(length / frame_rate)
            sequence.set_playback_start_seconds(0)
            unreal.EditorAssetLibrary.save_asset(f"{path}/{name}")
            return sequence
    except Exception as e:
        print(f"创建序列出错: {str(e)}")
    return None
def save_all_changes(level_subsystem):
    """保存所有更改"""
    level_subsystem.save_current_level()
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(
        save_map_packages=True,
        save_content_packages=True
    )
def create_gui():
    root = tk.Tk()
    root.title("UE5 Project Template Generator")
    root.geometry("400x200")
    
    # Project name input
    tk.Label(root, text="Project Name:").pack(pady=5)
    project_name_entry = tk.Entry(root)
    project_name_entry.pack(pady=5)
    
    # Shot count input
    tk.Label(root, text="Number of Shots:").pack(pady=5)
    shot_count_entry = tk.Entry(root)
    shot_count_entry.pack(pady=5)
    
    def on_generate():
        project_name = project_name_entry.get()
        try:
            shot_count = int(shot_count_entry.get())
            if shot_count <= 0:
                raise ValueError
            create_folder_structure(project_name, shot_count)
            messagebox.showinfo("Success", "Project structure generated successfully!")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number of shots!")
    
    # Generate button
    generate_btn = tk.Button(root, text="Generate Project Structure", command=on_generate)
    generate_btn.pack(pady=20)
    
    root.mainloop()
if __name__ == "__main__":
    create_gui()
