from functools import wraps
from flask import session, abort, render_template, request
from model.drivers.user_driver import UserDriver
from controller.utils import CustomLogger
from global_vars import DB_PATH, DEBUG

def route_access_required(allow_admin: bool = True):
    """
    Um decorador para proteger rotas baseado nos setores autorizados do usuário.
    
    Este decorador verifica se o usuário está logado e se tem acesso ao setor (blueprint) específico.
    Administradores têm acesso automático a tudo (a menos que allow_admin seja False).

    Parâmetros:
        allow_admin (bool): Se True, administradores têm acesso automático. Default: True.

    Retorna:
        Função decorada com a verificação de acesso por setor.

    Levanta:
        - `abort(403)`: Se o usuário não tiver acesso ao setor.
        - Redirecionamento para uma página de "não autorizado" se o usuário não estiver logado.
    """
    
    if callable(allow_admin):
        # Se o decorator for usado sem parênteses @route_access_required
        func = allow_admin
        allow_admin = True
        
        @wraps(func)
        def protected_route(*args, **kwargs):
            return _check_sector_access(func, True, *args, **kwargs)
        
        return protected_route
    
    # Se o decorator for usado com parênteses @route_access_required()
    def decorator_wrapper(func):
        @wraps(func)
        def protected_route(*args, **kwargs):
            return _check_sector_access(func, allow_admin, *args, **kwargs)
        
        return protected_route
    
    return decorator_wrapper


def _check_sector_access(view_function, allow_admin, *args, **kwargs):
    """
    Função auxiliar que realiza a verificação de acesso por setor.
    """
    # Obtém o usuário da sessão
    user = session.get('user')

    # Obtém o endpoint atual e extrai o setor
    current_endpoint = request.endpoint
    
    # Se não há endpoint, nega acesso
    if not current_endpoint:
        return abort(403)

    # Extrai o setor do endpoint
    try:
        from controller.route_utils import get_sector_from_endpoint
        current_sector = get_sector_from_endpoint(current_endpoint)
    except Exception:
        # Se não conseguir determinar o setor, nega acesso para não-admins
        if allow_admin and user and user.get('is_admin'):
            return view_function(*args, **kwargs)
        else:
            return abort(403)

    # Setor "Público" é acessível por todos (mesmo sem login)
    if current_sector == 'Público':
        return view_function(*args, **kwargs)

    # Se o usuário não estiver logado e não for setor público
    if not user:
        return render_template('not_allowed.html')

    # Setor "Comum" é acessível por todos os usuários logados
    if current_sector == 'Comum':
        return view_function(*args, **kwargs)

    # Se é admin e admin tem acesso automático
    if allow_admin and user.get('is_admin'):
        return view_function(*args, **kwargs)

    # Para outros setores, verificar autorização específica
    try:
        # Importa o driver de usuários para verificar acesso
        logger = CustomLogger(source="AUTH", debug=DEBUG)
        user_driver = UserDriver(logger=logger, db_path=DB_PATH)
        
        # Verifica se o usuário tem acesso ao setor atual
        has_access = user_driver.user_has_sector_access(user['email'], current_sector)
        
        if has_access:
            return view_function(*args, **kwargs)
        else:
            return abort(403)
                
    except Exception as e:
        # Em caso de erro no sistema de rotas, nega acesso para não-admins
        if allow_admin and user.get('is_admin'):
            return view_function(*args, **kwargs)
        else:
            return abort(403)

