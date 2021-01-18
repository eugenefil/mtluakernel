from ipykernel.kernelapp import IPKernelApp
from . import MTLuaKernel

# fyi launch_instance is not a method of IPKernelApp, but is inherited
# from IPython.core.application.BaseIPythonApplication which itself
# inherited it from traitlets.config.application.Application. And that
# traitlets project is used everywhere in jupyter for dynamic type
# checking and config parsing/storing. For introduction see
# https://labs.quansight.org/blog/2020/08/what-are-traitlets/.
IPKernelApp.launch_instance(kernel_class=MTLuaKernel)
