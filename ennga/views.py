from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET
from django.db import connection
import time


@require_GET
def health_check_view(request):
    """
    Lightweight health endpoint for UptimeRobot, Render, and automated monitors.
    Returns HTTP 200 OK to keep the Render web service awake and avoid sleeping.
    """
    check_db = request.GET.get('check_db') == '1'
    db_status = 'not_checked'

    if check_db:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                row = cursor.fetchone()
                db_status = 'connected' if row and row[0] == 1 else 'unexpected_result'
        except Exception as e:
            db_status = f'error: {str(e)}'

    # Plain text response if requested (e.g. ?format=text or curl)
    if request.GET.get('format') == 'text':
        return HttpResponse("OK", content_type="text/plain", status=200)

    return JsonResponse({
        'status': 'ok',
        'service': 'ennga-server',
        'database': db_status,
        'timestamp': int(time.time()),
    }, status=200)
