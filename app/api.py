import logging

import xlwings as xw
from fastapi import APIRouter, Body, Security

from .auth import User, authenticate, authorize

# Require authentication for all endpoints for this router
router = APIRouter(
    dependencies=[Security(authenticate)],
    prefix="",
    tags=["API"],
)

logger = logging.getLogger(__name__)


@router.post("/hello1")
def hello1(data: dict = Body):
    """This endpoint is protected by the router"""
    book = xw.Book(json=data)
    sheet = book.sheets[0]
    cell = sheet["A1"]
    if cell.value == "Hello xlwings!":
        cell.value = "Bye xlwings!"
    else:
        cell.value = "Hello xlwings!"
    return book.json()


@router.post("/hello2")
def hello2(data: dict = Body, current_user: User = Security(authenticate)):
    """This is how you access the user object"""
    book = xw.Book(json=data)
    sheet = book.sheets[0]
    cell = sheet["A2"]
    user_name = current_user.name
    if cell.value == f"Hello {user_name}!":
        cell.value = f"Bye {user_name}!"
    else:
        cell.value = f"Hello {user_name}!"
    return book.json()


@router.post("/hello3")
def hello3(
    data: dict = Body,
    current_user: User = Security(authorize, scopes=["Task.Write", "Task.Read"]),
):
    """RBAC: You can require specific roles by providing them as scopes:
    The implementation of authorize requires the user to have both
    the Taks.Read and the Taks.Write roles.
    """
    logger.info(f"hello3 called by {current_user.name} [{current_user.object_id}]")
    book = xw.Book(json=data)
    sheet = book.sheets[0]
    cell = sheet["A3"]
    user_name = current_user.name
    if cell.value == f"Hello {user_name}, you have the required roles!":
        cell.value = f"Bye {user_name}, you have the required roles!"
    else:
        cell.value = f"Hello {user_name}, you have the required roles!"
    return book.json()
