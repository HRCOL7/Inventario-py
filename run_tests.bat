@echo off
REM ===============================
REM IKARUS INVENTORY - Script de Testes
REM ===============================

echo.
echo ========================================
echo IKARUS INVENTORY - Executando Testes
echo ========================================
echo.

REM Verificar se pytest está instalado
pip list | findstr pytest >nul
if errorlevel 1 (
    echo Instalando pytest e coverage...
    pip install pytest pytest-cov coverage >nul 2>&1
)

echo [1] Executando testes unitários...
python -m pytest test_inventario.py -v

echo.
echo [2] Gerando relatório de cobertura...
python -m pytest test_inventario.py --cov=. --cov-report=html --cov-report=term

echo.
echo ========================================
echo Testes concluídos!
echo Relatório HTML em: htmlcov\index.html
echo ========================================
echo.
pause
