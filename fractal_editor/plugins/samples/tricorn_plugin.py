"""
トリコーンフラクタルのサンプルプラグイン。
複素共役を使用したフラクタルの実装例です。
"""
from ..developer_api import SimpleFractalGenerator, SimplePlugin, PluginDeveloperAPI


class TricornGenerator(SimpleFractalGenerator):
    """トリコーンフラクタル生成器。"""
    
    def __init__(self):
        super().__init__(
            name="トリコーン",
            description="トリコーンフラクタル - 複素共役を使用したマンデルブロ集合の変形"
        )
        
        # パラメータを追加
        self.add_parameter(
            PluginDeveloperAPI.create_parameter_definition(
                name="power",
                display_name="べき乗",
                param_type="float",
                default_value=2.0,
                min_value=1.0,
                max_value=5.0,
                description="フラクタルのべき乗値"
            )
        )
        
        self.add_parameter(
            PluginDeveloperAPI.create_parameter_definition(
                name="use_conjugate",
                display_name="複素共役を使用",
                param_type="bool",
                default_value=True,
                description="複素共役を使用するかどうか"
            )
        )
    
    def calculate_point(self, c: complex, max_iterations: int, **kwargs) -> int:
        """トリコーンフラクタルの計算。"""
        z = complex(0, 0)
        power = kwargs.get('power', 2.0)
        use_conjugate = kwargs.get('use_conjugate', True)
        
        for n in range(max_iterations):
            if abs(z) > 2.0:
                return n
            
            # トリコーンの特徴：複素共役を使用
            if use_conjugate:
                z = (z.conjugate()) ** power + c
            else:
                z = z ** power + c
        
        return max_iterations


class TricornPlugin(SimplePlugin):
    """トリコーンフラクタルプラグイン。"""
    
    def __init__(self):
        super().__init__(
            name="トリコーンフラクタル",
            version="1.0.0",
            author="フラクタルエディタ開発チーム",
            description="トリコーンフラクタルを生成するサンプルプラグイン",
            generator_factory=TricornGenerator
        )