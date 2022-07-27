import logging

from kanata import InjectableCatalog, LifetimeScope, find_injectables
from kanata.graphs.exceptions import CyclicGraphException

import structlog

from holobot.framework import Kernel
from holobot.framework.configs import Configurator
from holobot.framework.logging.processors import ignore_loggers_by_name
from holobot.framework.system import Environment
from holobot.sdk.logging.enums import LogLevel

if __name__ != "__main__":
    exit(0)

LOG_LEVEL_MAP = {
    LogLevel.NONE: logging.NOTSET,
    LogLevel.TRACE: logging.DEBUG,
    LogLevel.DEBUG: logging.DEBUG,
    LogLevel.INFORMATION: logging.INFO,
    LogLevel.WARNING: logging.WARN,
    LogLevel.ERROR: logging.ERROR,
    LogLevel.CRITICAL: logging.CRITICAL
}

# TODO Register the Environment/Configurator as instances in Kanata (not supported now).
environment = Environment()
configurator = Configurator(environment)
log_level = LogLevel.parse(configurator.get("General", "LogLevel", "Information"))

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        ignore_loggers_by_name("Kanata"),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper("iso"),
        structlog.dev.ConsoleRenderer()
    ],
    # TODO Replace with an AsyncBoundLogger when it's officially supported.
    # https://github.com/hynek/structlog/issues/354
    wrapper_class=structlog.make_filtering_bound_logger(LOG_LEVEL_MAP[log_level]),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True
)

logging.basicConfig(
    level=LOG_LEVEL_MAP[log_level],
    handlers=[
        
    ]
)

logger = structlog.get_logger("main")
logger.info("Configured logging", log_level=log_level.name or log_level.value)

# The idea here is to register the services for each extension independently,
# however, today it doesn't make sense as they're still in the same package.
# Therefore, for now we just register everything from the entire package.
registrations = find_injectables("holobot")
logger.info("Loaded all extensions")

catalog = InjectableCatalog(registrations)
scope = LifetimeScope(catalog)
try:
    logger.info("Starting the kernel...")
    scope.resolve(Kernel).run()
    logger.info("The kernel has stopped")
except CyclicGraphException as error:
    logger.fatal(
        "Failed to resolve the services, because there is a cycle in the dependency graph",
        nodes=", ".join(str(node) for node in error.nodes)
    )
