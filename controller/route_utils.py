from flask import current_app
from typing import List, Dict, Set


def get_all_application_routes() -> List[Dict[str, str]]:
    """
    Obtém todas as rotas da aplicação Flask dinamicamente
    
    :return: Lista de dicionários com informações das rotas
    """
    routes = []
    
    # Itera sobre todas as regras de URL registradas
    for rule in current_app.url_map.iter_rules():
        # Pula rotas estáticas
        if rule.endpoint == 'static':
            continue
            
        # Extrai informações da rota
        route_info = {
            'endpoint': rule.endpoint,
            'rule': rule.rule,
            'methods': list(rule.methods - {'HEAD', 'OPTIONS'}),  # Remove métodos internos
            'description': _format_endpoint_name(rule.endpoint)
        }
        
        routes.append(route_info)
    
    # Ordena as rotas por endpoint para facilitar a visualização
    routes.sort(key=lambda x: x['endpoint'])
    
    return routes


def _format_endpoint_name(endpoint: str) -> str:
    """
    Formata o nome do endpoint para uma descrição mais legível
    
    :param endpoint: Nome do endpoint
    :return: Nome formatado
    """
    # Remove o prefixo do blueprint
    if '.' in endpoint:
        blueprint_name, function_name = endpoint.split('.', 1)
        # Substitui underscores por espaços e capitaliza
        formatted_function = function_name.replace('_', ' ').title()
        return formatted_function
    else:
        # Substitui underscores por espaços e capitaliza
        return endpoint.replace('_', ' ').title()


def get_routes_sectors() -> Set[str]:
    """
    Obtém todos os setores (blueprints) disponíveis na aplicação
    Exclui apenas o setor "Público" que não deve ser selecionável
    
    :return: Set com os nomes dos setores selecionáveis
    """
    all_routes = get_all_application_routes()
    sectors = set()
    
    # Mapeamento de nomes de blueprint para nomes amigáveis
    sector_names = {
        'config': 'Configurações',
        'jornada': 'Jornada',
        'fechamento': 'Fechamento',
        'parametros': 'Parâmetros',
        'ssma': 'SSMA',
        'common': 'Comum',
        'public': 'Público'
    }
    
    # Setores que não devem ser selecionáveis no formulário
    non_selectable_sectors = {'Público'}  # Removido "Comum" - agora é obrigatório mas selecionável
    
    for route in all_routes:
        endpoint = route['endpoint']
        if '.' in endpoint:
            blueprint_name = endpoint.split('.')[0]
            # Usa o nome amigável se disponível, senão usa o nome do blueprint
            friendly_name = sector_names.get(blueprint_name, blueprint_name.title())
            
            # Só adiciona se não for um setor não-selecionável
            if friendly_name not in non_selectable_sectors:
                sectors.add(friendly_name)
    
    return sectors


def get_routes_by_category() -> Dict[str, List[Dict[str, str]]]:
    """
    Organiza as rotas em categorias para melhor visualização
    
    :return: Dicionário com rotas organizadas por categoria
    """
    all_routes = get_all_application_routes()
    
    categories = {
        'Principais': [],
        'Análise e Jornada': [],
        'Infrações': [],
        'Configurações': [],
        'APIs': [],
        'Outros': []
    }
    
    for route in all_routes:
        endpoint = route['endpoint']
        
        if any(main in endpoint for main in ['main_page', 'home', 'login', 'logout']):
            categories['Principais'].append(route)
        elif any(track in endpoint for track in ['track', 'jornada', 'insert_data', 'parameters', 'check_updates']):
            categories['Análise e Jornada'].append(route)
        elif 'infraction' in endpoint:
            categories['Infrações'].append(route)
        elif any(config in endpoint for config in ['config', 'manage', 'upload']):
            categories['Configurações'].append(route)
        elif 'routes_api' in endpoint:
            categories['APIs'].append(route)
        else:
            categories['Outros'].append(route)
    
    # Remove categorias vazias
    return {k: v for k, v in categories.items() if v}


def get_sector_from_endpoint(endpoint: str) -> str:
    """
    Extrai o setor (blueprint) de um endpoint
    
    :param endpoint: Nome do endpoint (ex: 'config.manage_users')
    :return: Nome do setor
    """
    if '.' not in endpoint:
        return 'public'
    
    blueprint_name = endpoint.split('.')[0]
    
        # Mapeamento de nomes de blueprint para nomes amigáveis
    sector_names = {
        'config': 'Configurações',
        'jornada': 'Jornada',
        'fechamento': 'Fechamento',
        'parametros': 'Parâmetros',
        'ssma': 'SSMA',
        'common': 'Comum',
        'public': 'Público'
    }
    
    return sector_names.get(blueprint_name, blueprint_name.title())


def is_protected_route(endpoint: str) -> bool:
    """
    Verifica se uma rota deve ser protegida por autenticação
    
    :param endpoint: Nome do endpoint
    :return: True se a rota deve ser protegida
    """
    # Rotas que não precisam de autenticação
    public_routes = ['public.login', 'static']
    
    return endpoint not in public_routes 