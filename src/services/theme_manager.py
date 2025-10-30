import json
import os
from pathlib import Path

class ThemeManager:
    """主题管理服务"""
    def __init__(self):
        self.themes_file = str(Path(__file__).parent.parent / 'support' / 'config' / 'themes.json')
        self.current_theme = 'default'
        self.load_themes()

    def load_themes(self):
        """从文件加载主题配置"""
        try:
            with open(self.themes_file, 'r', encoding='utf-8') as f:
                self.themes = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # 默认主题配置
            self.themes = {
                "default": {
                    "primary": "#2c7be5",
                    "secondary": "#6c757d",
                    "background": "#FFFFFF",
                    "text": "#333333",
                    "success": "#25A776",
                    "danger": "#EF4444"
                },
                "dark": {
                    "primary": "#0074D9",
                    "secondary": "#5a6268",
                    "background": "#121212",
                    "text": "#E0E0E0",
                    "success": "#3D9970",
                    "danger": "#FF4136"
                }
            }
            self.save_themes()

    def save_themes(self):
        """保存主题配置到文件"""
        os.makedirs(os.path.dirname(self.themes_file), exist_ok=True)
        with open(self.themes_file, 'w', encoding='utf-8') as f:
            json.dump(self.themes, f, indent=2, ensure_ascii=False)

    def get_theme(self, name=None):
        """获取指定主题配置"""
        return self.themes.get(name or self.current_theme, self.themes['default'])

    def get_all_themes(self):
        """获取所有主题列表"""
        return list(self.themes.keys())

    def save_theme(self, name, config):
        """保存自定义主题"""
        self.themes[name] = config
        self.save_themes()

    def delete_theme(self, name):
        """删除主题(默认主题不可删除)"""
        if name != 'default' and name in self.themes:
            del self.themes[name]
            self.save_themes()

    def apply_theme(self, fig, theme_name=None):
        """应用主题到图表(兼容旧版)"""
        theme = self.get_theme(theme_name)
        fig.update_layout(
            plot_bgcolor=theme.get('background', '#FFFFFF'),
            paper_bgcolor=theme.get('background', '#FFFFFF'),
            xaxis=dict(gridcolor=theme.get('secondary', '#E0E0E0')),
            yaxis=dict(gridcolor=theme.get('secondary', '#E0E0E0'))
        )
        return fig
