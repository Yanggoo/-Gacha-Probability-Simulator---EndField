"""
明日方舟·终末地 抽卡概率模拟器 - 图形界面
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from collections import Counter
from config import CharacterPoolConfig, WeaponPoolConfig, PlayerInfo, SimulationConfig
from weapon_gacha_utils import combined_character_weapon_simulation
from analysis_utils import plot_success_failure_pie, plot_combined_distributions


class GachaSimulatorUI:
    def __init__(self, root):
        self.root = root
        self.root.title("明日方舟·终末地 抽卡概率模拟器")
        self.root.geometry("800x900")
        
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 创建主容器和滚动条
        main_container = ttk.Frame(root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建Canvas和Scrollbar
        canvas = tk.Canvas(main_container)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 角色池当前状态
        char_state_frame = ttk.LabelFrame(scrollable_frame, text="角色池当前状态", padding=10)
        char_state_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(char_state_frame, text="已使用抽数:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.char_total_pulls = ttk.Entry(char_state_frame, width=15)
        self.char_total_pulls.insert(0, "0")
        self.char_total_pulls.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        self.char_limited_obtained = tk.BooleanVar()
        ttk.Checkbutton(char_state_frame, text="已获得限定角色", 
                       variable=self.char_limited_obtained).grid(
            row=1, column=0, columnspan=2, sticky=tk.W, pady=2
        )
        
        # 角色池保底状态（这些信息会用于计算内部状态）
        guarantee_frame = ttk.LabelFrame(scrollable_frame, text="角色池保底信息", padding=10)
        guarantee_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(guarantee_frame, text="N次内必得6星:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.got_six_star = ttk.Entry(guarantee_frame, width=15)
        self.got_six_star.insert(0, "80")
        self.got_six_star.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(guarantee_frame, text="N次内必得5星或以上:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.got_five_or_six = ttk.Entry(guarantee_frame, width=15)
        self.got_five_or_six.insert(0, "10")
        self.got_five_or_six.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # 角色池资源
        resource_frame = ttk.LabelFrame(scrollable_frame, text="角色池资源", padding=10)
        resource_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(resource_frame, text="十连寻访凭证数:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.char_ten_pulls = ttk.Entry(resource_frame, width=15)
        self.char_ten_pulls.insert(0, "0")
        self.char_ten_pulls.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(resource_frame, text="紧急招募十连数:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.char_urgent_pulls = ttk.Entry(resource_frame, width=15)
        self.char_urgent_pulls.insert(0, "0")
        self.char_urgent_pulls.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # 角色池目标
        char_goal_frame = ttk.LabelFrame(scrollable_frame, text="角色池目标", padding=10)
        char_goal_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(char_goal_frame, text="限定角色数量:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.char_limited_count = ttk.Entry(char_goal_frame, width=15)
        self.char_limited_count.insert(0, "0")
        self.char_limited_count.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(char_goal_frame, text="抽数上限(0=无限):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.char_pull_limit = ttk.Entry(char_goal_frame, width=15)
        self.char_pull_limit.insert(0, "0")
        self.char_pull_limit.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(char_goal_frame, text="抽数下限:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.char_pull_minimum = ttk.Entry(char_goal_frame, width=15)
        self.char_pull_minimum.insert(0, "0")
        self.char_pull_minimum.grid(row=2, column=1, sticky=tk.W, pady=2)
        
        # 武器池状态
        weapon_frame = ttk.LabelFrame(scrollable_frame, text="武器池当前状态", padding=10)
        weapon_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(weapon_frame, text="已使用十连次数:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.weapon_total_pulls = ttk.Entry(weapon_frame, width=15)
        self.weapon_total_pulls.insert(0, "0")
        self.weapon_total_pulls.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(weapon_frame, text="初始武器配额:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.initial_quota = ttk.Entry(weapon_frame, width=15)
        self.initial_quota.insert(0, "0")
        self.initial_quota.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # 武器池目标
        weapon_goal_frame = ttk.LabelFrame(scrollable_frame, text="武器池目标", padding=10)
        weapon_goal_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(weapon_goal_frame, text="限定武器数量:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.weapon_limited_count = ttk.Entry(weapon_goal_frame, width=15)
        self.weapon_limited_count.insert(0, "0")
        self.weapon_limited_count.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(weapon_goal_frame, text="十连次数上限(0=无限):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.weapon_pull_limit = ttk.Entry(weapon_goal_frame, width=15)
        self.weapon_pull_limit.insert(0, "0")
        self.weapon_pull_limit.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(weapon_goal_frame, text="十连次数下限:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.weapon_pull_minimum = ttk.Entry(weapon_goal_frame, width=15)
        self.weapon_pull_minimum.insert(0, "0")
        self.weapon_pull_minimum.grid(row=2, column=1, sticky=tk.W, pady=2)
        
        self.enable_char_on_low_quota = tk.BooleanVar(value=True)
        ttk.Checkbutton(weapon_goal_frame, text="配额不足时抽角色池，否则直接额外购买", 
                       variable=self.enable_char_on_low_quota).grid(
            row=3, column=0, columnspan=2, sticky=tk.W, pady=2
        )
        
        # 模拟配置
        sim_frame = ttk.LabelFrame(scrollable_frame, text="模拟配置", padding=10)
        sim_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(sim_frame, text="模拟次数:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.simulation_runs = ttk.Entry(sim_frame, width=15)
        self.simulation_runs.insert(0, "10000")
        self.simulation_runs.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        # 按钮和进度
        control_frame = ttk.Frame(scrollable_frame)
        control_frame.grid(row=7, column=0, columnspan=2, pady=10)
        
        self.run_button = ttk.Button(control_frame, text="开始模拟", command=self.run_simulation)
        self.run_button.pack(side=tk.LEFT, padx=5)
        
        self.progress = ttk.Progressbar(control_frame, length=300, mode='indeterminate')
        self.progress.pack(side=tk.LEFT, padx=5)
        
        # 结果显示
        result_frame = ttk.LabelFrame(scrollable_frame, text="模拟结果", padding=10)
        result_frame.grid(row=8, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.result_text = scrolledtext.ScrolledText(result_frame, width=80, height=15)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # 配置Canvas和Scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 绑定鼠标滚轮
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def validate_inputs(self):
        """验证输入"""
        try:
            # 验证所有数字输入并确保非负
            fields = [
                (self.char_total_pulls.get(), "当前限定池已使用抽数"),
                (self.got_six_star.get(), "N次内必得6星"),
                (self.got_five_or_six.get(), "N次内必得5星或以上"),
                (self.char_ten_pulls.get(), "十连寻访凭证数"),
                (self.char_urgent_pulls.get(), "紧急招募十连数"),
                (self.char_limited_count.get(), "限定角色数量"),
                (self.char_pull_limit.get(), "角色池抽数上限"),
                (self.char_pull_minimum.get(), "角色池抽数下限"),
                (self.weapon_total_pulls.get(), "武器池已使用十连次数"),
                (self.initial_quota.get(), "初始武器配额"),
                (self.weapon_limited_count.get(), "限定武器数量"),
                (self.weapon_pull_limit.get(), "武器池十连次数上限"),
                (self.weapon_pull_minimum.get(), "武器池十连次数下限"),
            ]
            
            for value, name in fields:
                num = int(value)
                if num < 0:
                    raise ValueError(f"{name}不能为负数")
            
            sim_runs = int(self.simulation_runs.get())
            if sim_runs <= 0:
                raise ValueError("模拟次数必须大于0")
            
            return True
        except ValueError as e:
            messagebox.showerror("输入错误", f"请检查输入的数值是否正确:\n{str(e)}")
            return False
    
    def create_player_info(self):
        """从UI创建PlayerInfo对象"""
        character_goals = {}
        limited_count = int(self.char_limited_count.get())
        character_goals["限定"] = limited_count
        
        weapon_goals = {}
        weapon_limited_count = int(self.weapon_limited_count.get())
        weapon_goals["限定武器"] = weapon_limited_count
        
        player_info = PlayerInfo(
            # 内部状态字段: character_soft_pity_accumulate 将由compute_internal_state()自动计算
            
            # 角色池当前状态
            character_total_pulls_used=int(self.char_total_pulls.get()),
            character_limited_obtained=self.char_limited_obtained.get(),
            
            # 保底信息
            got_six_star_character_in_next_pulls=int(self.got_six_star.get()),
            got_five_or_six_star_character_in_next_pulls=int(self.got_five_or_six.get()),
            character_ten_pulls_available=int(self.char_ten_pulls.get()),
            character_urgent_ten_pulls_available=int(self.char_urgent_pulls.get()),
            initial_weapon_quota=int(self.initial_quota.get()),
            
            # 角色池目标和策略
            character_goals=character_goals,
            character_pull_limit=int(self.char_pull_limit.get()),
            character_pull_minimum=int(self.char_pull_minimum.get()),
            character_always_pull_ten=False,  # 不暴露给玩家，默认为False
            
            # 武器池初始状态
            weapon_total_pulls_used=int(self.weapon_total_pulls.get()),
            weapon_limited_obtained=False,
            weapon_six_star_obtained=False,
            
            # 武器池目标和策略
            weapon_goals=weapon_goals,
            weapon_pull_limit=int(self.weapon_pull_limit.get()),
            weapon_pull_minimum=int(self.weapon_pull_minimum.get()),
            is_character_pull_enabled_on_low_quota=self.enable_char_on_low_quota.get()
        )
        
        return player_info
    
    def run_simulation_thread(self):
        """在后台线程运行模拟"""
        try:
            # 创建配置
            character_pool_config = CharacterPoolConfig()
            weapon_pool_config = WeaponPoolConfig()
            player_info = self.create_player_info()
            
            # 计算内部状态字段
            player_info.compute_internal_state(character_pool_config)
            
            sim_runs = int(self.simulation_runs.get())
            sim_config = SimulationConfig(simulation_runs=sim_runs)
            
            # 运行模拟
            results = []
            success_count = 0
            failure_reasons = Counter()
            
            for i in range(sim_config.simulation_runs):
                result = combined_character_weapon_simulation(
                    character_pool_config,
                    weapon_pool_config,
                    player_info
                )
                results.append(result)
                
                if result['成功']:
                    success_count += 1
                else:
                    failure_reason = result.get('失败原因', '未知原因')
                    failure_reasons[failure_reason] += 1
            
            # 计算成功率
            failure_count = sim_config.simulation_runs - success_count
            success_rate = success_count / sim_config.simulation_runs * 100
            
            # 绘制图表
            plot_success_failure_pie(success_count, failure_count, 
                                    save_path='combined_success_failure_pie.png',
                                    results=results)
            plot_combined_distributions(results, success_rate, save_prefix='combined_all')
            
            # 统计结果
            char_pulls_list = [r['角色总抽数（不含紧急）'] for r in results]
            weapon_pulls_list = [r['武器十连次数'] for r in results]
            remaining_quota_list = [r['剩余配额'] for r in results]
            extra_quota_list = [r['额外购买配额'] for r in results]
            
            result_msg = f"模拟完成！\n\n"
            result_msg += f"模拟次数: {sim_config.simulation_runs}\n"
            result_msg += f"成功次数: {success_count}\n"
            result_msg += f"失败次数: {failure_count}\n"
            result_msg += f"成功率: {success_rate:.2f}%\n\n"
            
            result_msg += f"角色池抽数统计（不含紧急）:\n"
            result_msg += f"  平均: {sum(char_pulls_list)/len(char_pulls_list):.2f}\n"
            result_msg += f"  最小: {min(char_pulls_list)}\n"
            result_msg += f"  最大: {max(char_pulls_list)}\n"
            result_msg += f"  中位数: {sorted(char_pulls_list)[len(char_pulls_list)//2]}\n\n"
            
            result_msg += f"武器池十连次数统计:\n"
            result_msg += f"  平均: {sum(weapon_pulls_list)/len(weapon_pulls_list):.2f}\n"
            result_msg += f"  最小: {min(weapon_pulls_list)}\n"
            result_msg += f"  最大: {max(weapon_pulls_list)}\n"
            result_msg += f"  中位数: {sorted(weapon_pulls_list)[len(weapon_pulls_list)//2]}\n\n"
            
            result_msg += f"剩余武库配额统计:\n"
            result_msg += f"  平均: {sum(remaining_quota_list)/len(remaining_quota_list):.2f}\n"
            result_msg += f"  最小: {min(remaining_quota_list)}\n"
            result_msg += f"  最大: {max(remaining_quota_list)}\n"
            result_msg += f"  中位数: {sorted(remaining_quota_list)[len(remaining_quota_list)//2]}\n\n"
            
            result_msg += f"额外购买武库配额统计:\n"
            result_msg += f"  平均: {sum(extra_quota_list)/len(extra_quota_list):.2f}\n"
            result_msg += f"  最小: {min(extra_quota_list)}\n"
            result_msg += f"  最大: {max(extra_quota_list)}\n"
            result_msg += f"  中位数: {sorted(extra_quota_list)[len(extra_quota_list)//2]}\n\n"
            
            if failure_reasons:
                result_msg += f"失败原因统计:\n"
                for reason, count in failure_reasons.most_common():
                    result_msg += f"  {reason}: {count} 次 ({count/failure_count*100:.1f}%)\n"
            
            result_msg += f"\n图片已保存到当前目录:\n"
            result_msg += f"  - combined_success_failure_pie.png\n"
            result_msg += f"  - combined_all_cdf.png\n"
            
            # 在主线程更新UI
            self.root.after(0, self.update_result, result_msg, True)
            
        except Exception as e:
            error_msg = f"模拟过程中发生错误:\n{str(e)}"
            self.root.after(0, self.update_result, error_msg, False)
    
    def update_result(self, message, success):
        """更新结果显示"""
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(1.0, message)
        self.progress.stop()
        self.run_button.config(state=tk.NORMAL)
        
        if success:
            messagebox.showinfo("完成", "模拟完成！图片已保存到当前目录。")
    
    def run_simulation(self):
        """启动模拟"""
        if not self.validate_inputs():
            return
        
        self.run_button.config(state=tk.DISABLED)
        self.progress.start()
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(1.0, "正在运行模拟，请稍候...\n")
        
        # 在后台线程运行
        thread = threading.Thread(target=self.run_simulation_thread, daemon=True)
        thread.start()
    
    def on_closing(self):
        """窗口关闭时的处理"""
        self.root.destroy()


def main():
    root = tk.Tk()
    app = GachaSimulatorUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
