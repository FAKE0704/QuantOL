class ThemeManager:
    """主题管理服务"""
    def __init__(self):
        self.themes = {
            'dark': {
                'bg_color': '#1E1E1E',
                'grid_color': '#404040',
                'up_color': '#25A776',
                'down_color': '#EF4444'
            },
            'light': {
                'bg_color': '#FFFFFF',
                'grid_color': '#E0E0E0',
                'up_color': '#10B981',
                'down_color': '#EF4444'
            }
        }
        self.current_theme = 'dark'

    def apply_theme(self, fig, theme_name=None):
        """应用主题到图表"""
        theme = self.themes[theme_name or self.current_theme]
        fig.update_layout(
            plot_bgcolor=theme['bg_color'],
            paper_bgcolor=theme['bg_color'],
            xaxis=dict(gridcolor=theme['grid_color']),
            yaxis=dict(gridcolor=theme['grid_color'])
        )
        return fig
