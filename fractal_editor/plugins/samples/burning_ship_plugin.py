"""
バーニングシップフラクタルのサンプルプラグイン。
プラグイン開発の参考実装として提供されます。
"""
from ..developer_api import SimpleFractalGenerator, SimplePlugin, PluginDeveloperAPI


class BurningShipGenerator(SimpleFractalGenerator):
    """バーニングシップフラクタル生成器。"""
    
    def __init__(self):
        super().__init__(
            name="バーニングシップ",
            description="バーニングシップフラクタル - 絶対値を使用した変形マンデルブロ集合"
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
                name="escape_radius",
                display_name="発散半径",
                param_type="float",
                default_value=2.0,
                min_value=1.0,
                max_value=10.0,
                description="発散判定の半径"
            )
        )
    
    def calculate_point(self, c: complex, max_iterations: int, **kwargs) -> int:
        """バーニングシップフラクタルの計算。"""
        z = complex(0, 0)
        power = kwargs.get('power', 2.0)
        escape_radius = kwargs.get('escape_radius', 2.0)
        
        for n in range(max_iterations):
            if abs(z) > escape_radius:
                return n
            
            # バーニングシップの特徴：実部と虚部の絶対値を取る
            z = complex(abs(z.real), abs(z.imag)) ** power + c
        
        return max_iterations


class BurningShipPlugin(SimplePlugin):
    """バーニングシップフラクタルプラグイン。"""
    
    def __init__(self):
        super().__init__(
            name="バーニングシップフラクタル",
            version="1.0.0",
            author="フラクタルエディタ開発チーム",
            description="バーニングシップフラクタルを生成するサンプルプラグイン",
            generator_factory=BurningShipGenerator
        )