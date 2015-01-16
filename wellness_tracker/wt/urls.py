from django.conf.urls import patterns, url
from wt import views

# for django to pick up mapping must use name 'urlpatterns'
urlpatterns = patterns( '',
    url( r'^$', views.home, name='home'),
    url( r'^graph/(?P<user_id>\d+)/', views.graph, name='user_graph'),
    url( r'^graph/', views.graph, name='graph'),
    url( r'^questions/', views.questions, name='questions'),
    url( r'^patients/', views.patient_list, name='patient_list'),
    url( r'^planning/(?P<user_id>\d+)/', views.planning, name='planning'),
    url( r'^goal_summary/(?P<user_id>\d+)/', views.goal_summary, name='goal_summary'),
    url( r'^overall_summary/(?P<user_id>\d+)/', views.overall_summary, name='overall_summary'),
    url( r'^new_strategy/(?P<user_id>\d+)/', views.new_strategy, name='new_strategy'),
    url( r'^new_strategy_planning/(?P<user_id>\d+)/', views.new_strategy_planning, name='new_strategy_planning'),
    url( r'^new_strategy_selection/(?P<user_id>\d+)/', views.new_strategy_selection, name='new_strategy_selection'),
    url( r'^createpatient/', views.create_patient, name='create_patient'),
    url( r'^new_question/(?P<user_id>\d+)/', views.new_question,     name='new_question'),
    url( r'^appendix_va', views.appendix_va, name='appendix_va'),
    url( r'^appendix_vb', views.appendix_vb, name='appendix_vb'),
    url( r'^gas_step1/(?P<user_id>\d+)/', views.gas_step1, name='gas_step1'),
    url( r'^gas_goal_selection/(?P<user_id>\d+)/', views.gas_goal_selection, name='gas_goal_selection'),
    url( r'^new_strategy/(?P<user_id>\d+)/', views.new_strategy, name='new_strategy'),
	url( r'^profile/', views.profile, name='profile'),
    url( r'^add_so/', views.add_so, name='add_so'),
)
