from fastapi import APIRouter, UploadFile, File

router = APIRouter()

@router.post("/upload")
def upload_screenshot(file: UploadFile = File(...)):
    """
    Upload a screenshot from the employee agent
    """
    return {"filename": file.filename}
