from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Any, List, cast, get_args, get_origin


from agieval.common.cache import Cache
from agieval.common.logger import log, log_debug, log_warn, log_error
from agieval.entity.eval_config import EvalConfig
from agieval.entity.flow_config import PluginConfig, PluginType
from agieval.core.plugin.base_plugin_param import BasePluginParam, BaseStagePluginParam, BaseStepPluginParam

T = TypeVar('T', bound=BasePluginParam)  # Define generic type, limited to BasePluginParam subclasses
class BasePlugin(ABC, Generic[T]):

    """
    BasePlugin is the base class for plugins, all plugins need to inherit from this class.
    Currently, no interfaces need to be defined in the base class.
    """
    plugin_type: PluginType 
    def __init__(self, args: dict[str, Any]):
        _param_class = self.__class__.get_generic_param_type()
        self.context_param: T = cast(T, _param_class.model_validate(args))
        Cache.init(self.context_param.work_dir)
    
    @classmethod
    def get_generic_param_type(cls) -> type[T]:
        # Process of getting generic parameters
        assert hasattr(cls, "__orig_bases__"), "Plugin implementation class definition does not conform to specifications"
        orig_bases = getattr(cls, "__orig_bases__")
        assert len(orig_bases) > 0, "Plugin implementation class definition does not conform to specifications"
        orig_base = orig_bases[0]
        assert issubclass(get_origin(orig_base), BasePlugin), "Plugin implementation class definition does not conform to specifications"
        generic_args = get_args(orig_base)
        assert len(generic_args) > 0, "Plugin implementation class definition does not conform to specifications"
        _param_class = generic_args[0]
        assert issubclass(_param_class, BasePluginParam), "Plugin implementation class definition does not conform to specifications"
        return cast(type[T], _param_class)

    
    @abstractmethod
    def run(self, *args, **kwargs):
        """
        Root plugin execution entry
        """
        pass
    
    def log(self, x, **kwargs):
        log(x, **kwargs)
    def log_debug(self, x, **kwargs):
        log_debug(x, **kwargs)
    def log_warn(self, x, **kwargs):
        log_warn(x, **kwargs)
    def log_error(self, x, **kwargs):
        log_error(x, **kwargs)



Stage = TypeVar('Stage', bound=BaseStagePluginParam)
class BaseStage(BasePlugin[Stage]):

    def run(self, plugin_list: List[PluginConfig], eval_config: EvalConfig):
        self.plugin_list = plugin_list
        self.eval_config = eval_config

        if self.use_cache():
            return
        
        from agieval.core.plugin.plugin_factory import PluginFactory
        PluginFactory.find_plugins(plugin_list)
        self.process()
        

    @abstractmethod
    def process(self):
        pass

    @staticmethod
    def get_steps() -> list[PluginType]:
        raise NotImplementedError("Subclasses of BaseStage must implement the static method get_steps(), returning the set of processing steps for this stage")
    
    @abstractmethod
    def cache_is_available(self) -> bool:
        """
        Determine if cache is available, if cache is available, skip current stage execution
        """
        raise NotImplementedError("Subclasses of BaseStage must implement the method cache_is_available(), returning whether cache data is available")

    @classmethod
    def get_default_plugin_param(cls) -> BaseStagePluginParam:
        return cls.get_generic_param_type()()

    def use_cache(self) -> bool:
        if not self.context_param.use_cache:
            return False
        if self.cache_is_available():
            self.log(f"Plugin {self.__class__.__name__} uses cached data, skipping this execution")
            return True
        return False


Step = TypeVar('Step', bound=BaseStepPluginParam)
class BaseStep(BasePlugin[Step]):
    
    @classmethod
    def get_default_plugin_param(cls) -> BaseStepPluginParam:
        return cls.get_generic_param_type()()
        

