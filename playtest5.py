import re
import requests
import json
import os
import time
import hashlib
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import pygame
from PIL import Image, ImageTk
import prettytable as pt


class MusicPlayerApp:
    def __init__(self, root):
        """初始化音乐播放器应用"""
        self.root = root
        self.root.title("音乐播放器")
        self.root.geometry("800x600")
        self.root.resizable(False, False)

        # 确保中文显示正常
        self.setup_fonts()

        # 初始化pygame混音器
        pygame.mixer.init()

        # 应用状态变量
        self.current_folder = ""
        self.current_playlist = []
        self.current_index = 0
        self.playing = False
        self.paused = False
        self.volume = 0.5

        # 酷狗音乐API配置
        self.headers = {
            "cookie": "kg_mid=a43a75749fa6ccbf8b414bde36ff04e8; kg_dfid=2UHKbv1RUXdS2AlFVn2Rxmsx; kg_dfid_collect=d41d8cd98f00b204e9800998ecf8427e; Hm_lvt_aedee6983d4cfc62f509129360d6bb3d=1748958398; HMACCOUNT=A16E2A2915FE305C; KuGoo=KugooID=2084751082&KugooPwd=9EF49E0B2C9C35EDE93AEB6BA6AFDD37&NickName=%u7b49%u5f85%u82b1%u5b63&Pic=http://imge.kugou.com/kugouicon/165/20240526/20240526095845957397.jpg&RegState=1&RegFrom=&t=03f83b58f448249c64e282e891a81acd7ab5cb39d449312346c121960d58defd&t_ts=1748958507&t_key=&a_id=1014&ct=1748958507&UserName=%u006b%u0067%u006f%u0070%u0065%u006e%u0032%u0030%u0038%u0034%u0037%u0035%u0031%u0030%u0038%u0032; KugooID=2084751082; t=03f83b58f448249c64e282e891a81acd7ab5cb39d449312346c121960d58defd; a_id=1014; UserName=%u006b%u0067%u006f%u0070%u0065%u006e%u0032%u0030%u0038%u0034%u0037%u0035%u0031%u0030%u0038%u0032; mid=a43a75749fa6ccbf8b414bde36ff04e8; dfid=2UHKbv1RUXdS2AlFVn2Rxmsx; kg_mid_temp=a43a75749fa6ccbf8b414bde36ff04e8;Hm_lpvt_aedee6983d4cfc62f509129360d6bb3d=1748961485",
            "referer": "https://www.kugou.com/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0"
        }
        self.date = int(time.time() * 1000)
        self.dfid = '2UHKbv1RUXdS2AlFVn2Rxmsx'
        self.mid = 'a43a75749fa6ccbf8b414bde36ff04e8'
        self.token = '03f83b58f448249c64e282e891a81acd8b5797b8267241f62c67fb6065f1e156'
        self.uuid = 'a43a75749fa6ccbf8b414bde36ff04e8'

        # 创建UI
        self.create_widgets()

        # 初始化音乐文件夹
        self.default_music_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "music")
        os.makedirs(self.default_music_folder, exist_ok=True)
        self.load_music_folder(self.default_music_folder)  # 加载该文件夹内容

        # 搜索结果存储
        self.search_results = []

    def setup_fonts(self):
        """确保中文显示正常"""
        # 尝试设置多种中文字体
        font_names = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC", "Microsoft YaHei"]
        for font_name in font_names:
            try:
                # 尝试使用字体创建一个标签
                test_label = tk.Label(self.root, text="测试", font=(font_name, 10))
                test_label.pack()
                test_label.destroy()  # 立即销毁测试标签
                # 如果没有抛出异常，则使用该字体
                self.default_font = (font_name, 10)
                return
            except:
                continue
        # 如果没有找到中文字体，则使用默认字体
        self.default_font = ("Arial", 10)

    def create_widgets(self):
        """创建应用界面"""
        # 设置背景图片
        try:
            # 尝试加载背景图片
            self.bg_image = Image.open("dog.gif")  # 请替换为您的图片路径
            self.bg_image = self.bg_image.resize((800, 600), Image.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(self.bg_image)

            # 创建一个Canvas作为背景
            self.canvas = tk.Canvas(self.root, width=800, height=600)
            self.canvas.pack(fill=tk.BOTH, expand=True)
            self.canvas.create_image(0, 0, image=self.bg_photo, anchor=tk.NW)

            # 创建一个透明的Frame作为主容器，放在Canvas上
            self.main_frame = ttk.Frame(self.canvas, padding="10")
            self.canvas_frame = self.canvas.create_window((0, 0), window=self.main_frame, anchor=tk.NW)

            # 配置Canvas滚动
            self.canvas.bind("<Configure>", self._on_resize)
        except Exception as e:
            print(f"加载背景图片失败: {e}")
            # 如果加载失败，使用普通Frame作为主容器
            self.main_frame = ttk.Frame(self.root, padding="10")
            self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 顶部搜索框 - 添加到main_frame而不是root
        search_frame = ttk.Frame(self.main_frame, padding="10")
        search_frame.pack(fill=tk.X)

        ttk.Label(search_frame, text="搜索音乐:", font=self.default_font).pack(side=tk.LEFT, padx=5)
        self.search_entry = ttk.Entry(search_frame, width=30, font=self.default_font)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_button = ttk.Button(search_frame, text="搜索", command=self.search_music, width=10)
        self.search_button.pack(side=tk.LEFT, padx=5)

        # 主内容区域 - 添加到main_frame
        content_frame = ttk.Frame(self.main_frame, padding="10")
        content_frame.pack(fill=tk.BOTH, expand=True)

        # 左侧播放列表
        ttk.Label(content_frame, text="播放列表", font=self.default_font).pack(anchor=tk.W)
        playlist_frame = ttk.Frame(content_frame)
        playlist_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.playlist_box = tk.Listbox(playlist_frame, width=40, height=20, font=self.default_font)
        self.playlist_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.playlist_scroll = ttk.Scrollbar(playlist_frame, orient=tk.VERTICAL, command=self.playlist_box.yview)
        self.playlist_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.playlist_box.config(yscrollcommand=self.playlist_scroll.set)
        self.playlist_box.bind("<Double-1>", self.play_selected)

        # 右侧搜索结果
        search_results_frame = ttk.Frame(content_frame)
        search_results_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        ttk.Label(search_results_frame, text="搜索结果", font=self.default_font).pack(anchor=tk.W)

        # 搜索结果列表
        self.search_results_box = tk.Listbox(search_results_frame, width=40, height=18, font=self.default_font)
        self.search_results_box.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.search_results_scroll = ttk.Scrollbar(search_results_frame, orient=tk.VERTICAL,
                                                     command=self.search_results_box.yview)
        self.search_results_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.search_results_box.config(yscrollcommand=self.search_results_scroll.set)

        # 新增"全部下载"按钮
        self.download_all_button = ttk.Button(
            search_results_frame,
            text="全部下载",
            command=self.download_all_music,
            width=15
        )
        self.download_all_button.pack(side=tk.BOTTOM, pady=2)

        # 下载按钮
        self.download_button = ttk.Button(search_results_frame, text="添加到播放列表", command=self.download_and_play,
                                          width=15)
        self.download_button.pack(side=tk.BOTTOM, pady=5)

        # 底部控制区域 - 添加到main_frame
        control_frame = ttk.Frame(self.main_frame, padding="10")
        control_frame.pack(fill=tk.X)

        # 音量控制
        volume_frame = ttk.Frame(control_frame)
        volume_frame.pack(side=tk.LEFT, padx=5)

        ttk.Label(volume_frame, text="音量:", font=self.default_font).pack(side=tk.LEFT)
        self.volume_scale = ttk.Scale(volume_frame, from_=0, to=1, orient=tk.HORIZONTAL,
                                      length=100, value=self.volume, command=self.set_volume)
        self.volume_scale.pack(side=tk.LEFT, padx=5)

        # 播放控制按钮
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(side=tk.LEFT, padx=20)

        self.prev_button = ttk.Button(button_frame, text="上一首", command=self.play_previous, width=8)
        self.prev_button.pack(side=tk.LEFT, padx=2)

        self.play_button = ttk.Button(button_frame, text="播放", command=self.toggle_playback, width=8)
        self.play_button.pack(side=tk.LEFT, padx=2)

        self.stop_button = ttk.Button(button_frame, text="停止", command=self.stop_playback, width=8)
        self.stop_button.pack(side=tk.LEFT, padx=2)

        self.next_button = ttk.Button(button_frame, text="下一首", command=self.play_next, width=8)
        self.next_button.pack(side=tk.LEFT, padx=2)

        # 当前播放信息
        info_frame = ttk.Frame(control_frame)
        info_frame.pack(side=tk.RIGHT, padx=5)

        self.current_song_var = tk.StringVar(value="当前播放: 无")
        self.current_song_label = ttk.Label(info_frame, textvariable=self.current_song_var, font=self.default_font)
        self.current_song_label.pack(side=tk.LEFT)

        # 菜单
        self.create_menu()

        # 确保主框架尺寸与Canvas一致
        self.root.update_idletasks()
        self.canvas.itemconfig(self.canvas_frame, width=self.canvas.winfo_width())

        # 配置Canvas滚动
        self.canvas.bind("<Configure>", self._on_resize)

    def _on_resize(self, event):
        """处理窗口大小变化事件"""
        if hasattr(self, 'canvas') and hasattr(self, 'canvas_frame'):
            self.canvas.itemconfig(self.canvas_frame, width=event.width)

    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="打开文件夹", command=self.open_folder)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        menubar.add_cascade(label="文件", menu=file_menu)

        self.root.config(menu=menubar)

    def load_music_folder(self, folder_path):
        """加载指定文件夹中的音乐文件"""
        self.current_folder = folder_path
        self.current_playlist = []

        try:
            files = os.listdir(folder_path)
            for file in files:
                if file.endswith(('.mp3', '.wav', '.ogg', '.flac')):
                    self.current_playlist.append(os.path.join(folder_path, file))

            self.update_playlist_display()

            if self.current_playlist:
                self.current_song_var.set(f"当前播放: {os.path.basename(self.current_playlist[0])}")
            else:
                self.current_song_var.set("当前播放: 无")

            return True
        except Exception as e:
            messagebox.showerror("错误", f"加载文件夹失败: {str(e)}")
            return False

    def update_playlist_display(self):
        """更新播放列表显示"""
        self.playlist_box.delete(0, tk.END)
        for song in self.current_playlist:
            self.playlist_box.insert(tk.END, os.path.basename(song))

    def open_folder(self):
        """打开文件夹选择对话框"""
        folder = filedialog.askdirectory()
        if folder:
            self.load_music_folder(folder)

    def _md5_hash_search(self, word):
        """生成搜索接口的签名"""
        text = [
            'NVPh5oo715z5DIWAeQlhMDsWXXQV4hwt',
            'appid=1014',
            'bitrate=0',
            'callback=callback123',
            f'clienttime={self.date}',
            'clientver=1000',
            f'dfid={self.dfid}',
            'filter=10',
            'inputtype=0',
            'iscorrection=1',
            'isfuzzy=0',
            f'keyword={word}',
            f'mid={self.mid}',
            'page=1',
            'pagesize=30',
            'platform=WebFilter',
            'privilege_filter=0',
            'srcappid=2919',
            f'token={self.token}',
            'userid=2084751082',
            f'uuid={self.uuid}',
            'NVPh5oo715z5DIWAeQlhMDsWXXQV4hwt'
        ]
        string = ''.join(text)
        md5 = hashlib.md5()
        md5.update(string.encode('utf-8'))
        return md5.hexdigest()

    def _md5_hash_save(self, music_id):
        """生成下载接口的签名"""
        text = [
            'NVPh5oo715z5DIWAeQlhMDsWXXQV4hwt',
            'appid=1014',
            f'clienttime={self.date}',
            'clientver=20000',
            f'dfid={self.dfid}',
            f'encode_album_audio_id={music_id}',
            f'mid={self.mid}',
            'platid=4',
            'srcappid=2919',
            f'token={self.token}',
            'userid=2084751082',
            f'uuid={self.uuid}',
            'NVPh5oo715z5DIWAeQlhMDsWXXQV4hwt'
        ]
        string = ''.join(text)
        md5 = hashlib.md5()
        md5.update(string.encode('utf-8'))
        return md5.hexdigest()

    def save(self, music_id):
        """下载指定ID的歌曲"""
        signature = self._md5_hash_save(music_id)

        # 请求链接,数据包接口
        url = 'https://wwwapi.kugou.com/play/songinfo'
        # 请求参数
        data = {
            "srcappid": "2919",
            "clientver": "20000",
            "clienttime": self.date,
            'mid': self.mid,
            'uuid': self.uuid,
            'dfid': self.dfid,
            "appid": '1014',
            "platid": '4',
            'encode_album_audio_id': music_id,
            'token': self.token,
            'userid': '2084751082',
            'signature': signature
        }

        # 发送请求
        response = requests.get(url=url, params=data, headers=self.headers)

        # 解析数据
        try:
            song_name = response.json()['data']['song_name']
            singer_name = response.json()['data']['author_name']
            play_url = response.json()['data']['play_url']
        except (KeyError, json.JSONDecodeError) as e:
            messagebox.showerror("错误", f"解析歌曲信息失败: {str(e)}")
            return None

        # 确保保存目录存在
        save_dir = self.default_music_folder
        os.makedirs(save_dir, exist_ok=True)

        # 安全处理文件名
        safe_title = re.sub(r'[<>:"/\\|?*]', '', song_name)  # 过滤非法字符
        safe_singer = re.sub(r'[<>:"/\\|?*]', '', singer_name)
        safe_filename = f"{safe_title}-{safe_singer}.mp3"  # 格式：歌曲名-歌手.mp3
        file_path = os.path.join(save_dir, safe_filename)

        # 检查文件是否已存在
        if os.path.exists(file_path):
            print(f"文件已存在: {safe_filename}")
            return file_path  # 已存在则直接返回路径

        # 下载音频
        try:
            music_content = requests.get(play_url, headers=self.headers, stream=True).content
        except Exception as e:
            messagebox.showerror("错误", f"下载歌曲失败: {str(e)}")
            return None

        # 保存文件
        try:
            with open(file_path, 'wb') as f:
                f.write(music_content)
            print(f"下载成功: {safe_filename}")
        except Exception as e:
            messagebox.showerror("错误", f"保存歌曲失败: {str(e)}")
            return None

        return file_path

    def search_music(self):
        """搜索歌曲/歌手"""
        keyword = self.search_entry.get().strip()
        if not keyword:
            messagebox.showinfo("提示", "请输入搜索关键词")
            return

        self.search_results_box.delete(0, tk.END)
        self.search_button.config(state=tk.DISABLED)
        self.search_entry.config(state=tk.DISABLED)

        # 在后台线程中执行搜索
        threading.Thread(target=self._search_music_thread, args=(keyword,), daemon=True).start()

    def _search_music_thread(self, keyword):
        """在后台线程中执行音乐搜索"""
        try:
            signature = self._md5_hash_search(keyword)

            # 发送请求
            link = 'https://complexsearch.kugou.com/v2/search/song'
            link_data = {
                'callback': 'callback123',
                'srcappid': '2919',
                'clientver': '1000',
                'clienttime': self.date,
                'mid': self.mid,
                'uuid': self.uuid,
                'dfid': self.dfid,
                'keyword': keyword,
                'page': 1,
                'pagesize': 30,
                'bitrate': 0,
                'isfuzzy': 0,
                'inputtype': 0,
                'platform': 'WebFilter',
                'userid': '2084751082',
                'iscorrection': 1,
                'privilege_filter': 0,
                'filter': 10,
                'token': self.token,
                'appid': '1014',
                'signature': signature,
            }

            # 获取数据
            response = requests.get(url=link, params=link_data, headers=self.headers)

            # 解析数据
            html_data = re.findall('callback123\((.*)', response.text)[0].replace(')', '')
            json_data = json.loads(html_data)

            # 显示搜索结果
            self.search_results = []

            for i, index in enumerate(json_data['data']['lists'], 1):
                song_info = {
                    "歌名": index['SongName'],
                    "歌手": index['SingerName'],
                    "专辑": index['AlbumName'],
                    "ID": index['EMixSongID']
                }
                self.search_results.append(song_info)
                display_text = f"{i}. {index['SongName']} - {index['SingerName']}"
                self.root.after(0, lambda text=display_text: self.search_results_box.insert(tk.END, text))

            if not self.search_results:
                self.root.after(0, lambda: messagebox.showinfo("提示", "未找到相关音乐"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"搜索出错: {str(e)}"))
        finally:
            self.root.after(0, lambda: self.search_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.search_entry.config(state=tk.NORMAL))

    def download_all_music(self):
        """批量下载所有搜索结果中的歌曲"""
        if not self.search_results:
            messagebox.showinfo("提示", "当前无搜索结果")
            return

        # 确认是否开始批量下载
        if messagebox.askyesno("确认", f"即将下载 {len(self.search_results)} 首歌曲，是否继续？"):
            # 在后台线程中执行批量下载
            threading.Thread(target=self._download_all_thread, daemon=True).start()

    def _download_all_thread(self):
        """后台线程执行批量下载"""
        success_count = 0
        fail_count = 0
        total = len(self.search_results)

        try:
            self.root.after(0, lambda: self.download_all_button.config(state=tk.DISABLED))
            self.root.after(0, lambda: messagebox.showinfo("提示", f"开始下载 {total} 首歌曲..."))

            for i, song in enumerate(self.search_results, 1):
                music_id = song.get("ID", "")
                if not music_id:
                    fail_count += 1
                    continue

                # 调用下载函数
                file_path = self.save(music_id)
                if file_path:
                    success_count += 1
                    # 每5首歌曲显示一次进度
                    if i % 5 == 0:
                        self.root.after(0, lambda cnt=i: messagebox.showinfo("进度", f"已下载 {cnt} 首"))
                else:
                    fail_count += 1

                # 添加下载间隔，避免频繁请求被封IP
                time.sleep(1)

            # 下载完成后更新播放列表并提示结果
            self.root.after(0, lambda: self.load_music_folder(self.default_music_folder))
            result_msg = f"下载完成！\n成功：{success_count} 首\n失败：{fail_count} 首"
            self.root.after(0, lambda: messagebox.showinfo("结果", result_msg))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"批量下载出错：{str(e)}"))
        finally:
            self.root.after(0, lambda: self.download_all_button.config(state=tk.NORMAL))

    def download_and_play(self):
        """下载并播放选中的音乐"""
        selection = self.search_results_box.curselection()
        if not selection:
            messagebox.showinfo("提示", "请先选择要下载的歌曲")
            return

        index = selection[0]
        if index >= len(self.search_results):
            messagebox.showinfo("提示", "无效的选择")
            return

        song = self.search_results[index]
        music_id = song.get("ID", "")

        if not music_id:
            messagebox.showerror("错误", "无法获取歌曲信息")
            return

        # 在后台线程中执行下载
        threading.Thread(target=self._download_and_play_thread, args=(music_id,), daemon=True).start()

    def _download_and_play_thread(self, music_id):
        """在后台线程中执行音乐下载并播放"""
        try:
            # 更新UI状态
            self.root.after(0, lambda: self.download_button.config(state=tk.DISABLED))

            # 下载音乐
            file_path = self.save(music_id)

            if file_path:
                # 更新UI状态
                self.root.after(0, lambda: messagebox.showinfo("成功", f"下载完成"))

                # 更新播放列表
                self.root.after(0, lambda: self.load_music_folder(self.default_music_folder))

                # 播放新下载的歌曲
                # 找到新下载的歌曲在列表中的位置
                try:
                    index = self.current_playlist.index(file_path)
                    self.root.after(0, lambda idx=index: self.play_song_by_index(idx))
                except ValueError:
                    self.root.after(0, lambda: messagebox.showinfo("提示", "下载的歌曲未添加到播放列表中"))
            else:
                self.root.after(0, lambda: messagebox.showerror("错误", "下载失败"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"下载出错: {str(e)}"))
        finally:
            self.root.after(0, lambda: self.download_button.config(state=tk.NORMAL))

    def play_song_by_index(self, index):
        """通过索引播放歌曲"""
        if 0 <= index < len(self.current_playlist):
            self.current_index = index
            self.play_song(self.current_playlist[index])

    def play_song(self, song_path):
        """播放指定歌曲"""
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(song_path)
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play()

            self.playing = True
            self.paused = False

            # 更新当前播放歌曲信息
            self.current_song_var.set(f"当前播放: {os.path.basename(song_path)}")

            # 更新播放列表选中项
            if song_path in self.current_playlist:
                index = self.current_playlist.index(song_path)
                self.playlist_box.selection_clear(0, tk.END)
                self.playlist_box.selection_set(index)
                self.playlist_box.see(index)
                self.current_index = index

            # 更新按钮状态
            self.play_button.config(text="暂停")

            # 监听音乐播放结束
            threading.Thread(target=self._monitor_playback, daemon=True).start()
        except Exception as e:
            messagebox.showerror("错误", f"播放失败: {str(e)}")

    def play_selected(self, event=None):
        """播放选中的歌曲"""
        selection = self.playlist_box.curselection()
        if selection:
            index = selection[0]
            song_path = self.current_playlist[index]
            self.play_song(song_path)

    def toggle_playback(self):
        """切换播放/暂停状态"""
        if not self.current_playlist:
            messagebox.showinfo("提示", "播放列表为空")
            return

        if self.playing:
            if self.paused:
                pygame.mixer.music.unpause()
                self.paused = False
                self.play_button.config(text="暂停")
            else:
                pygame.mixer.music.pause()
                self.paused = True
                self.play_button.config(text="继续")
        else:
            # 如果没有播放任何歌曲，则播放第一首
            self.play_song(self.current_playlist[self.current_index])

    def stop_playback(self):
        """停止播放"""
        pygame.mixer.music.stop()
        self.playing = False
        self.paused = False
        self.play_button.config(text="播放")

    def play_next(self):
        """播放下一首"""
        if not self.current_playlist:
            return

        self.current_index = (self.current_index + 1) % len(self.current_playlist)
        self.play_song(self.current_playlist[self.current_index])

    def play_previous(self):
        """播放上一首"""
        if not self.current_playlist:
            return

        self.current_index = (self.current_index - 1) % len(self.current_playlist)
        self.play_song(self.current_playlist[self.current_index])

    def set_volume(self, value):
        """设置音量"""
        self.volume = float(value)
        pygame.mixer.music.set_volume(self.volume)

    def _monitor_playback(self):
        """监控音乐播放状态，自动播放下一首"""
        while self.playing:
            if not pygame.mixer.music.get_busy() and not self.paused:
                # 音乐播放结束，自动播放下一首
                self.root.after(0, self.play_next)
                break
            time.sleep(0.5)


if __name__ == "__main__":
    root = tk.Tk()
    app = MusicPlayerApp(root)
    root.mainloop()