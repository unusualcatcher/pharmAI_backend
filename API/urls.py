from django.urls import path
from .views import (
    iqvia_api, 
    clinical_trials_api, 
    exim_trade_api, 
    patent_landscape_api, 
    internal_knowledge_base_api,
    patent_analysis_api  
)

urlpatterns = [
    path('iqvia/', iqvia_api, name='iqvia'),
    path('clinical-trials/', clinical_trials_api, name='clinical_trials'),
    path('exim-trade/', exim_trade_api, name='exim_trade'),
    path('patents/', patent_landscape_api, name='patent_landscape'),
    path('knowledge-base/', internal_knowledge_base_api, name='knowledge_base'),
    path('patent-analysis/', patent_analysis_api, name='patent_analysis'),
]
