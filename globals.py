class UserType:
    default = "user"
    user = "user"  # пользователь
    moderator = "moderator"  # модератор
    admin = "admin"  # админ
    level1 = [admin, moderator]
    level2 = [admin]


# Transaction types
class OfferType:
    default = ""
    goto = "goto"  # между пользователями
    check = "check"  # зачисление налички
    win = "win"  # зачисление за игру


# Names and strings
class Naming:
    site_name = "LetMeCook"
    coin_name = "<a href='https://t.me/city_heroes'>\"LetMeCook\"</a>"
    coin_name_out_link = "\"LetMeCook\""
    tgk_name = "https://t.me/city_heroes"


list_of_banned_words = ("сука шваль мразь тварь гад чмо дебил дурак долбоеб ебать трах сволочь мразота член пизда "
                        "вагина хуй украин войн").split()


def check_for_banned(st: str):
    for w in list_of_banned_words:
        if st.lower().count(w) > 0:
            return False
    return ("cво" not in st.lower().split()) and ("гойда" not in st.lower().split())  # СПЕЦИАЛЬНО ДЛЯ АНТОНА


def reason_return(st: str):
    if st == TransactionType.default:
        return "Неопределено"
    if st == TransactionType.check:
        return "Начисление"
    if st == TransactionType.goto:
        return "Перевод"
    if st == TransactionType.win:
        return "Выигрыш в конкурсе"