from django.urls import path
from .views import ModuleListView, InstallModuleView, UninstallModuleView, UpgradeModuleView

app_name = 'module'  # This is crucial for namespace to work

urlpatterns = [
    path('', ModuleListView.as_view(), name='module_list'),
    path('upgrade/<int:module_id>/', UpgradeModuleView.as_view(), name='upgrade_module'),
    path('install/<int:module_id>/', InstallModuleView.as_view(), name='install_module'),
    path('uninstall/<int:module_id>/', UninstallModuleView.as_view(), name='uninstall_module'),
]
