from django.urls import path
from . import views

urlpatterns = [
    path('agent/stream/', views.stream_agent_chat, name='agent_stream'),
    path('agent/chat/', views.chat_agent, name='agent_chat'),
    path('agent/health/', views.health_check, name='agent_health'),
    path('agent/demo/', views.demo,name='demo')
]
