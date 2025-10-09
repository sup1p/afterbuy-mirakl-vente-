from fastapi import APIRouter, Depends, HTTPException, UploadFile, Query
import json
from pathlib import Path
from typing import List, Dict, Any

from src.core.dependencies import get_current_user
import logging
from logs.config_logs import setup_logging

setup_logging()

logger = logging.getLogger(__name__)


router = APIRouter()

@router.post("/upload-json-fabric-jv", tags=["import files"])
async def upload_json_fabric_jv(
    file: UploadFile, 
    current_user = Depends(get_current_user)
):
    """
    Принимает ТОЛЬКО JSON файлы и сохраняет их в backend/src/const/import_data/fabrics_jv/
    """
    try:
        # Проверяем, что файл является JSON
        if not file.filename.lower().endswith('.json'):
            raise HTTPException(
                status_code=400,
                detail="Только JSON файлы разрешены для загрузки"
            )
        
        # Проверяем content type
        if file.content_type and not file.content_type.startswith('application/json'):
            # Позволяем также text/plain для JSON файлов
            if not file.content_type.startswith('text/plain'):
                raise HTTPException(
                    status_code=400,
                    detail=f"Неверный тип файла. Ожидается application/json, получен {file.content_type}"
                )
        
        # Читаем содержимое файла
        content = await file.read()
        
        # Валидируем, что это корректный JSON
        try:
            json_data = json.loads(content.decode('utf-8'))
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Неверный формат JSON: {str(e)}"
            )
        except UnicodeDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Ошибка кодировки файла: {str(e)}"
            )
        
        # Определяем путь для сохранения
        save_dir = Path("backend/src/const/import_data/fabrics_jv")
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Сохраняем файл (заменяем если существует)
        original_filename = file.filename
        save_path = save_dir / original_filename
        
        # Сохраняем файл
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        # Проверяем, что файл действительно сохранен
        if not save_path.exists():
            raise HTTPException(
                status_code=500,
                detail="Файл не был сохранен. Проверьте права доступа к директории."
            )
        
        logger.info(f"JSON file saved successfully: {save_path}")
        
        return {
            "message": "JSON файл успешно загружен и сохранен",
            "filename": save_path.name,
            "path": str(save_path),
            "size": len(content),
            "records_count": len(json_data) if isinstance(json_data, list) else 1,
            "replaced": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading JSON fabric file: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при загрузке файла: {str(e)}"
        )
        
        
@router.post("/upload-json-fabric-xl", tags=["import files"])
async def upload_json_fabric_xl(
    file: UploadFile, 
    current_user = Depends(get_current_user)
):
    """
    Принимает ТОЛЬКО JSON файлы и сохраняет их в backend/src/const/import_data/fabrics_jv/
    """
    try:
        # Проверяем, что файл является JSON
        if not file.filename.lower().endswith('.json'):
            raise HTTPException(
                status_code=400,
                detail="Только JSON файлы разрешены для загрузки"
            )
        
        # Проверяем content type
        if file.content_type and not file.content_type.startswith('application/json'):
            # Позволяем также text/plain для JSON файлов
            if not file.content_type.startswith('text/plain'):
                raise HTTPException(
                    status_code=400,
                    detail=f"Неверный тип файла. Ожидается application/json, получен {file.content_type}"
                )
        
        # Читаем содержимое файла
        content = await file.read()
        
        # Валидируем, что это корректный JSON
        try:
            json_data = json.loads(content.decode('utf-8'))
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Неверный формат JSON: {str(e)}"
            )
        except UnicodeDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Ошибка кодировки файла: {str(e)}"
            )
        
        # Определяем путь для сохранения
        save_dir = Path("backend/src/const/import_data/fabrics_xl")
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Сохраняем файл (заменяем если существует)
        original_filename = file.filename
        save_path = save_dir / original_filename
        
        # Сохраняем файл
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        # Проверяем, что файл действительно сохранен
        if not save_path.exists():
            raise HTTPException(
                status_code=500,
                detail="Файл не был сохранен. Проверьте права доступа к директории."
            )
        
        logger.info(f"JSON file saved successfully: {save_path}")
        
        return {
            "message": "JSON файл успешно загружен и сохранен",
            "filename": save_path.name,
            "path": str(save_path),
            "size": len(content),
            "records_count": len(json_data) if isinstance(json_data, list) else 1,
            "replaced": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading JSON fabric file: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при загрузке файла: {str(e)}"
        )
        
        
        
@router.post("/upload-html-jv", tags=["import files"])
async def upload_html_jv(
    file: UploadFile, 
    current_user = Depends(get_current_user)
):
    """
    Принимает ТОЛЬКО HTML файлы и сохраняет их в backend/src/const/import_data/HTML_jv/
    """
    try:
        # Проверяем, что файл является HTML
        if not file.filename.lower().endswith('.html'):
            raise HTTPException(
                status_code=400,
                detail="Только HTML файлы разрешены для загрузки"
            )
        
        # Проверяем content type
        if file.content_type and not file.content_type.startswith('text/html'):
            # Позволяем также text/plain для HTML файлов
            if not file.content_type.startswith('text/plain'):
                raise HTTPException(
                    status_code=400,
                    detail=f"Неверный тип файла. Ожидается text/html, получен {file.content_type}"
                )
        
        # Читаем содержимое файла
        content = await file.read()
        
        # Валидируем кодировку
        try:
            html_content = content.decode('utf-8')
        except UnicodeDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Ошибка кодировки файла: {str(e)}"
            )
        
        # Определяем путь для сохранения
        save_dir = Path("backend/src/const/import_data/HTML_jv")
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Сохраняем файл (заменяем если существует)
        original_filename = file.filename
        save_path = save_dir / original_filename
        
        # Сохраняем файл
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Проверяем, что файл действительно сохранен
        if not save_path.exists():
            raise HTTPException(
                status_code=500,
                detail="Файл не был сохранен. Проверьте права доступа к директории."
            )
        
        logger.info(f"HTML file saved successfully: {save_path}")
        
        return {
            "message": "HTML файл успешно загружен и сохранен",
            "filename": save_path.name,
            "path": str(save_path),
            "size": len(content),
            "replaced": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading HTML file: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при загрузке файла: {str(e)}"
        )
        
        
@router.post("/upload-html-xl", tags=["import files"])
async def upload_html_xl(
    file: UploadFile, 
    current_user = Depends(get_current_user)
):
    """
    Принимает ТОЛЬКО HTML файлы и сохраняет их в backend/src/const/import_data/HTML_xl/
    """
    try:
        # Проверяем, что файл является HTML
        if not file.filename.lower().endswith('.html'):
            raise HTTPException(
                status_code=400,
                detail="Только HTML файлы разрешены для загрузки"
            )
        
        # Проверяем content type
        if file.content_type and not file.content_type.startswith('text/html'):
            # Позволяем также text/plain для HTML файлов
            if not file.content_type.startswith('text/plain'):
                raise HTTPException(
                    status_code=400,
                    detail=f"Неверный тип файла. Ожидается text/html, получен {file.content_type}"
                )
        
        # Читаем содержимое файла
        content = await file.read()
        
        # Валидируем кодировку
        try:
            html_content = content.decode('utf-8')
        except UnicodeDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Ошибка кодировки файла: {str(e)}"
            )
        
        # Определяем путь для сохранения
        save_dir = Path("backend/src/const/import_data/HTML_xl")
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Сохраняем файл (заменяем если существует)
        original_filename = file.filename
        save_path = save_dir / original_filename
        
        # Сохраняем файл
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Проверяем, что файл действительно сохранен
        if not save_path.exists():
            raise HTTPException(
                status_code=500,
                detail="Файл не был сохранен. Проверьте права доступа к директории."
            )
        
        logger.info(f"HTML file saved successfully: {save_path}")
        
        return {
            "message": "HTML файл успешно загружен и сохранен",
            "filename": save_path.name,
            "path": str(save_path),
            "size": len(content),
            "replaced": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading HTML file: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при загрузке файла: {str(e)}"
        )


@router.get("/list-json-fabric-jv", tags=["import files"])
async def list_json_fabric_jv(
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
    limit: int = Query(10, ge=1, le=100, description="Количество файлов на странице"),
    current_user = Depends(get_current_user)
):
    """
    Возвращает список JSON файлов из папки fabrics_jv с пагинацией
    """
    try:
        files_dir = Path("backend/src/const/import_data/fabrics_jv")
        
        if not files_dir.exists():
            return {
                "files": [],
                "total": 0,
                "offset": offset,
                "limit": limit,
                "message": "Папка с файлами не существует"
            }
        
        # Получаем все JSON файлы и сортируем по имени
        all_files = sorted([f for f in files_dir.iterdir() if f.is_file() and f.suffix.lower() == '.json'], key=lambda x: x.name)
        total_files = len(all_files)
        
        # Применяем пагинацию
        paginated_files = all_files[offset:offset + limit]
        
        # Формируем информацию о файлах
        files_info = []
        for file_path in paginated_files:
            try:
                file_stat = file_path.stat()
                files_info.append({
                    "filename": file_path.name,
                    "path": str(file_path),
                    "size": file_stat.st_size,
                    "created": file_stat.st_ctime,
                    "modified": file_stat.st_mtime
                })
            except Exception as e:
                logger.error(f"Error getting file info for {file_path}: {e}")
                files_info.append({
                    "filename": file_path.name,
                    "path": str(file_path),
                    "error": f"Ошибка получения информации: {str(e)}"
                })
        
        return {
            "files": files_info,
            "total": total_files,
            "offset": offset,
            "limit": limit,
            "has_more": offset + limit < total_files
        }
        
    except Exception as e:
        logger.error(f"Error listing JSON fabric JV files: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении списка файлов: {str(e)}"
        )


@router.get("/list-json-fabric-xl", tags=["import files"])
async def list_json_fabric_xl(
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
    limit: int = Query(10, ge=1, le=100, description="Количество файлов на странице"),
    current_user = Depends(get_current_user)
):
    """
    Возвращает список JSON файлов из папки fabrics_xl с пагинацией
    """
    try:
        files_dir = Path("backend/src/const/import_data/fabrics_xl")
        
        if not files_dir.exists():
            return {
                "files": [],
                "total": 0,
                "offset": offset,
                "limit": limit,
                "message": "Папка с файлами не существует"
            }
        
        # Получаем все JSON файлы и сортируем по имени
        all_files = sorted([f for f in files_dir.iterdir() if f.is_file() and f.suffix.lower() == '.json'], key=lambda x: x.name)
        total_files = len(all_files)
        
        # Применяем пагинацию
        paginated_files = all_files[offset:offset + limit]
        
        # Формируем информацию о файлах
        files_info = []
        for file_path in paginated_files:
            try:
                file_stat = file_path.stat()
                files_info.append({
                    "filename": file_path.name,
                    "path": str(file_path),
                    "size": file_stat.st_size,
                    "created": file_stat.st_ctime,
                    "modified": file_stat.st_mtime
                })
            except Exception as e:
                logger.error(f"Error getting file info for {file_path}: {e}")
                files_info.append({
                    "filename": file_path.name,
                    "path": str(file_path),
                    "error": f"Ошибка получения информации: {str(e)}"
                })
        
        return {
            "files": files_info,
            "total": total_files,
            "offset": offset,
            "limit": limit,
            "has_more": offset + limit < total_files
        }
        
    except Exception as e:
        logger.error(f"Error listing JSON fabric XL files: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении списка файлов: {str(e)}"
        )


@router.get("/list-html-jv", tags=["import files"])
async def list_html_jv(
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
    limit: int = Query(10, ge=1, le=100, description="Количество файлов на странице"),
    current_user = Depends(get_current_user)
):
    """
    Возвращает список HTML файлов из папки HTML_jv с пагинацией
    """
    try:
        files_dir = Path("backend/src/const/import_data/HTML_jv")
        
        if not files_dir.exists():
            return {
                "files": [],
                "total": 0,
                "offset": offset,
                "limit": limit,
                "message": "Папка с файлами не существует"
            }
        
        # Получаем все HTML файлы и сортируем по имени
        all_files = sorted([f for f in files_dir.iterdir() if f.is_file() and f.suffix.lower() == '.html'], key=lambda x: x.name)
        total_files = len(all_files)
        
        # Применяем пагинацию
        paginated_files = all_files[offset:offset + limit]
        
        # Формируем информацию о файлах
        files_info = []
        for file_path in paginated_files:
            try:
                file_stat = file_path.stat()
                files_info.append({
                    "filename": file_path.name,
                    "path": str(file_path),
                    "size": file_stat.st_size,
                    "created": file_stat.st_ctime,
                    "modified": file_stat.st_mtime
                })
            except Exception as e:
                logger.error(f"Error getting file info for {file_path}: {e}")
                files_info.append({
                    "filename": file_path.name,
                    "path": str(file_path),
                    "error": f"Ошибка получения информации: {str(e)}"
                })
        
        return {
            "files": files_info,
            "total": total_files,
            "offset": offset,
            "limit": limit,
            "has_more": offset + limit < total_files
        }
        
    except Exception as e:
        logger.error(f"Error listing HTML JV files: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении списка файлов: {str(e)}"
        )


@router.get("/list-html-xl", tags=["import files"])
async def list_html_xl(
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
    limit: int = Query(10, ge=1, le=100, description="Количество файлов на странице"),
    current_user = Depends(get_current_user)
):
    """
    Возвращает список HTML файлов из папки HTML_xl с пагинацией
    """
    try:
        files_dir = Path("backend/src/const/import_data/HTML_xl")
        
        if not files_dir.exists():
            return {
                "files": [],
                "total": 0,
                "offset": offset,
                "limit": limit,
                "message": "Папка с файлами не существует"
            }
        
        # Получаем все HTML файлы и сортируем по имени
        all_files = sorted([f for f in files_dir.iterdir() if f.is_file() and f.suffix.lower() == '.html'], key=lambda x: x.name)
        total_files = len(all_files)
        
        # Применяем пагинацию
        paginated_files = all_files[offset:offset + limit]
        
        # Формируем информацию о файлах
        files_info = []
        for file_path in paginated_files:
            try:
                file_stat = file_path.stat()
                files_info.append({
                    "filename": file_path.name,
                    "path": str(file_path),
                    "size": file_stat.st_size,
                    "created": file_stat.st_ctime,
                    "modified": file_stat.st_mtime
                })
            except Exception as e:
                logger.error(f"Error getting file info for {file_path}: {e}")
                files_info.append({
                    "filename": file_path.name,
                    "path": str(file_path),
                    "error": f"Ошибка получения информации: {str(e)}"
                })
        
        return {
            "files": files_info,
            "total": total_files,
            "offset": offset,
            "limit": limit,
            "has_more": offset + limit < total_files
        }
        
    except Exception as e:
        logger.error(f"Error listing HTML XL files: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении списка файлов: {str(e)}"
        )