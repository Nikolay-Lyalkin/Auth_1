class UserNotFound(Exception):
    detail = "Имя пользователя и(или) пароль не совпадают"


class UserInDB(Exception):
    detail = "Пользователь с таким логином уже существует"
