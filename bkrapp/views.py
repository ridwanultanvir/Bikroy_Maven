from django.shortcuts import render
from django.db import connection
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
import hashlib

def index(request):
    user_id = request.session.get('user_id', 0)
    if user_id == 0:
        request.session['user_id'] = 0
        fullname = None
        no_products = None
        comp_id = None
    else:
        cursor = connection.cursor()
        sql = "SELECT F_NAME || ' ' || L_NAME FROM PERSON WHERE ID = %s"
        cursor.execute(sql, [user_id])
        result = cursor.fetchall()
        cursor.close()
        fullname = result[0][0]

        cursor = connection.cursor()
        sql = "SELECT NUMBER_OF_PRODUCT(%s) FROM DUAL"
        cursor.execute(sql, [user_id])
        result = cursor.fetchall()
        cursor.close()
        no_products = result[0][0]

        cursor = connection.cursor()
        sql = "SELECT COMPANY_ID FROM COMPANY WHERE MANAGER_ID = %s"
        cursor.execute(sql, [user_id])
        result = cursor.fetchall()
        cursor.close()
        comp_id = -1 if len(result) == 0 else result[0][0]
    context = {
        "user_id": user_id,
        "fullname": fullname,
        "no_products": no_products,
        "comp_id": comp_id
    }
    return render(request, 'index.html', context)

def profile(request):
    user_id = request.session.get('user_id', 0)
    cursor = connection.cursor()
    sql = "SELECT F_NAME, L_NAME, STREET, ZIP_CODE, HOUSE, AREA_ID, PHONE_NO FROM PERSON WHERE ID = %s"
    cursor.execute(sql, [user_id])
    result = cursor.fetchall()
    cursor.close()
    r = result[0]

    cursor = connection.cursor()
    sql = "SELECT AREA_NAME, (SELECT DIST_NAME FROM DISTRICTS D WHERE D.DIST_ID = A.DIST_ID) FROM AREAS A WHERE A.AREA_ID = %s"
    cursor.execute(sql, [r[5]])
    result = cursor.fetchall()
    cursor.close()
    area_name = result[0][0]
    dist_name = result[0][1]

    context = {
        "f_name": r[0],
        "l_name": r[1],
        "street": r[2],
        "zip": r[3],
        "house": r[4],
        "area": area_name,
        "phone": r[6],
        "dist_name": dist_name
    }

    return render(request, 'profile.html', context)

def applicant_info(request, applicant_id):
    user_id = request.session.get('user_id', 0)
    cursor = connection.cursor()
    sql = "SELECT MANAGER_ID FROM COMPANY WHERE COMPANY_ID IN (SELECT COMPANY_ID FROM JOB WHERE JOB_ID IN (SELECT JOB_ID FROM JOB_APPLICATION WHERE APPLICANT_ID = %s))"
    cursor.execute(sql, [applicant_id])
    result = cursor.fetchall()
    cursor.close()
    if any(user_id in r for r in result) is False:
        return render(request, 'error.html', {"message": "You don't have access to view this page"})

    cursor = connection.cursor()
    sql = "SELECT F_NAME, L_NAME, STREET, ZIP_CODE, HOUSE, AREA_ID, PHONE_NO FROM PERSON WHERE ID = %s"
    cursor.execute(sql, [applicant_id])
    result = cursor.fetchall()
    cursor.close()
    r = result[0]

    cursor = connection.cursor()
    sql = "SELECT AREA_NAME, (SELECT DIST_NAME FROM DISTRICTS D WHERE D.DIST_ID = A.DIST_ID) FROM AREAS A WHERE A.AREA_ID = %s"
    cursor.execute(sql, [r[5]])
    result = cursor.fetchall()
    cursor.close()
    area_name = result[0][0]
    dist_name = result[0][1]

    context = {
        "f_name": r[0],
        "l_name": r[1],
        "street": r[2],
        "zip": r[3],
        "house": r[4],
        "area": area_name,
        "phone": r[6],
        "dist_name": dist_name
    }

    return render(request, 'applicant_info.html', context)

def success_delete(request):
    user_id = request.session.get('user_id', 0)
    cursor = connection.cursor()
    deletesql = "DELETE FROM PERSON WHERE ID = %s"
    cursor.execute(deletesql, [user_id])
    connection.commit()
    cursor.close()

    request.session['user_id'] = 0
    return render(request, 'success_delete.html')

def check_delete(request):
    return render(request, 'check_delete.html')

def apply_job(request, job_id):
    user_id = request.session.get('user_id', 0)
    cursor = connection.cursor()
    # sql = "SELECT PRODUCT_ID, PRODUCT_NAME, AREA_ID FROM PRODUCT WHERE AREA_ID = %s"
    sql = "SELECT JOB_ID FROM JOB_APPLICATION WHERE JOB_ID = %s AND APPLICANT_ID = %s"
    cursor.execute(sql, [job_id, user_id])
    result = cursor.fetchall()
    cursor.close()

    # print("# job_id=", job_id, "\tuser_id=", user_id,"*********\n")

    if len(result) != 0:
        # print("\n\n***already applied for this job***\n\n")
        return render(request, "applied_once.html")

    else:
        cursor = connection.cursor()
        insertsql = "INSERT INTO JOB_APPLICATION(JOB_ID, APPLICANT_ID) VALUES (%s, %s)"
        cursor.execute(insertsql, [job_id, user_id])
        connection.commit()
        cursor.close()
        return HttpResponseRedirect(reverse("job_types"))

def delete_product(request, product_id):
    cursor = connection.cursor()
    deletesql = "DELETE FROM PRODUCT WHERE PRODUCT_ID = %s"
    cursor.execute(deletesql, [product_id])
    connection.commit()
    cursor.close()
    return HttpResponseRedirect(reverse("user_products"))

def edit_product(request, product_id):
    user_id = request.session.get('user_id', 0)

    cursor = connection.cursor()
    sql = "SELECT CATEGORY_ID FROM SUB_CATEGORIES WHERE SUBCAT_ID = (SELECT SUBCAT_ID FROM PRODUCT WHERE PRODUCT_ID = %s)"
    cursor.execute(sql, [product_id])
    result = cursor.fetchall()
    cursor.close()

    cursor = connection.cursor()
    sql = "SELECT CATEGORY_ID FROM SUB_CATEGORIES WHERE SUBCAT_ID = (SELECT SUBCAT_ID FROM PRODUCT WHERE PRODUCT_ID = %s)"
    cursor.execute(sql, [product_id])
    result = cursor.fetchall()
    cursor.close()
    cat_id = result[0][0]

    cursor = connection.cursor()
    sql = "SELECT PRODUCT_NAME, PRICE, STOCK, IMAGE, DESCRIPTION, SUBCAT_ID, ADVERTISER_ID FROM PRODUCT WHERE PRODUCT_ID = %s"
    cursor.execute(sql, [product_id])
    result = cursor.fetchall()
    cursor.close()
    r = result[0]

    cursor = connection.cursor()
    sql = "SELECT F_NAME || ' ' || L_NAME FROM PERSON WHERE ID = %s"
    cursor.execute(sql, [r[6]])
    result = cursor.fetchall()
    cursor.close()
    fullname = result[0][0]

    context = {
        "user_id": user_id,
        "fullname": fullname,
        "advertiser_id": r[6],
        "cat_id": cat_id,
        "product_id": product_id,
        "product_name": r[0],
        "price": r[1],
        "stock": r[2],
        "imgpath": r[3],
        "description": r[4] if r[4] else "",
        "subcat_id": r[5]
    }
    return render(request, 'edit_product.html',context)

def edit_product_action(request, product_id):
    # user_id = request.session.get('user_id', 0)
    try:
        product_name = request.POST['product_name']
        cursor = connection.cursor()
        updatesql = "UPDATE PRODUCT SET PRODUCT_NAME = %s WHERE PRODUCT_ID = %s"
        cursor.execute(updatesql, [product_name, product_id])
        connection.commit()
        cursor.close()
    except KeyError:
        pass

    try:
        price = request.POST['price']
        cursor = connection.cursor()
        updatesql = "UPDATE PRODUCT SET PRICE = %s WHERE PRODUCT_ID = %s"
        cursor.execute(updatesql, [price, product_id])
        connection.commit()
        cursor.close()
    except KeyError:
        pass

    try:
        stock = request.POST['stock']
        cursor = connection.cursor()
        updatesql = "UPDATE PRODUCT SET STOCK = %s WHERE PRODUCT_ID = %s"
        cursor.execute(updatesql, [stock, product_id])
        connection.commit()
        cursor.close()
    except KeyError:
        pass

    try:
        description = request.POST['description']
        cursor = connection.cursor()
        updatesql = "UPDATE PRODUCT SET DESCRIPTION = %s WHERE PRODUCT_ID = %s"
        cursor.execute(updatesql, [description, product_id])
        connection.commit()
        cursor.close()
    except KeyError:
        pass

    return HttpResponseRedirect(reverse("product_desc", args = (product_id, )))

def edit_profile(request):
    cursor = connection.cursor()
    sql = "SELECT * FROM DIVISIONS ORDER BY div_id"
    cursor.execute(sql)
    result = cursor.fetchall()
    cursor.close()
    divs = []
    for r in result:
        divs.append({'div_id': r[0], 'div_name': r[1]})

    cursor = connection.cursor()
    sql = "SELECT * FROM DISTRICTS"
    cursor.execute(sql)
    result = cursor.fetchall()
    cursor.close()
    dists = []
    for r in result:
        dists.append({'dist_id': r[0], 'dist_name': r[1], 'div_id': r[2]})

    user_id = request.session.get('user_id', 0)
    cursor = connection.cursor()
    sql = "SELECT F_NAME, L_NAME, STREET, ZIP_CODE, HOUSE, AREA_ID, PHONE_NO FROM PERSON WHERE ID = %s"
    cursor.execute(sql, [user_id])
    result = cursor.fetchall()
    cursor.close()
    r = result[0]
    person = []
    person.append({'f_name': r[0], 'l_name': r[1], 'street': r[2] if r[2] else '', 'zip_code': r[3] if r[3] else '', 'house': r[4] if r[4] else '', 'area_id': r[5], 'phone_no': r[6]})

    cursor = connection.cursor()
    sql = "SELECT AREA_NAME, DIST_ID FROM AREAS WHERE AREA_ID = %s"
    cursor.execute(sql, [r[5]])
    result = cursor.fetchall()
    cursor.close()
    area_name = result[0][0]
    dist_id = result[0][1]

    cursor = connection.cursor()
    sql = "SELECT DIV_ID FROM DISTRICTS WHERE DIST_ID = %s"
    cursor.execute(sql, [dist_id])
    result = cursor.fetchall()
    cursor.close()
    div_id = result[0][0]

    context = {
        "person": person,
        "area_name": area_name,
        "dist_id": dist_id,
        "div_id": div_id,
        "divs": divs,
        "dists": dists
    }
    return render(request, 'edit_profile.html', context)

def edit_profile_action(request):
    user_id = request.session.get('user_id', 0)
    try:
        f_name = request.POST['f_name']
        l_name = request.POST['l_name']
        phone = request.POST['phone']
        cursor = connection.cursor()
        updatesql = "UPDATE PERSON SET F_NAME = %s, L_NAME = %s, PHONE_NO = %s WHERE ID = %s"
        cursor.execute(updatesql, [f_name, l_name, phone, user_id])
        connection.commit()
        cursor.close()
    except KeyError:
        return render(request, 'error.html', {"message": "Couldn't update your account :("})
    try:
        street = request.POST['street']
        cursor = connection.cursor()
        updatesql = "UPDATE PERSON SET STREET = %s WHERE ID = %s"
        cursor.execute(updatesql, [street, user_id])
        connection.commit()
        cursor.close()
    except KeyError:
        pass

    try:
        zip = request.POST['zip']
        cursor = connection.cursor()
        updatesql = "UPDATE PERSON SET ZIP_CODE = %s WHERE ID = %s"
        cursor.execute(updatesql, [zip, user_id])
        connection.commit()
        cursor.close()
    except KeyError:
        pass

    try:
        house = request.POST['house']
        cursor = connection.cursor()
        updatesql = "UPDATE PERSON SET HOUSE = %s WHERE ID = %s"
        cursor.execute(updatesql, [house, user_id])
        connection.commit()
        cursor.close()
    except KeyError:
        pass

    return HttpResponseRedirect(reverse("profile"))

def user_jobs(request):
    user_id = request.session.get('user_id', 0)
    if user_id == 0:
        request.session['user_id'] = 0
        return HttpResponseRedirect(reverse("index"))
    else:
        cursor = connection.cursor()
        sql = "SELECT COMPANY_ID, COMPANY_NAME FROM COMPANY WHERE MANAGER_ID = %s"
        cursor.execute(sql, [user_id])
        result = cursor.fetchall()
        cursor.close()
        company_id = -1 if len(result) == 0 else result[0][0]
        company_name = result[0][1]
        # print("\n\n\n\n\n******** company_name =", company_name)

        cursor = connection.cursor()
        sql = "SELECT job_id, job_title FROM JOB WHERE COMPANY_ID = %s ORDER BY job_id"
        cursor.execute(sql, [company_id])
        result = cursor.fetchall()
        cursor.close()
        jobs = []
        for r in result:
            jobs.append({'job_id': r[0], 'job_title': r[1]})
            print("job_title=", r[1])
        context = {
            "user_id": user_id,
            "company_id": company_id,
            "company_name": company_name,
            "jobs": jobs
        }
        return render(request, "user_jobs.html", context)

def user_products(request):
    user_id = request.session.get('user_id', 0)
    cursor = connection.cursor()
    sql = "SELECT PRODUCT_ID, PRODUCT_NAME FROM PRODUCT WHERE ADVERTISER_ID = %s"
    cursor.execute(sql, [user_id])
    result = cursor.fetchall()
    cursor.close()
    products = []
    for r in result:
        products.append({'product_id': r[0], 'product_name': r[1]})
    context = {
        "user_id": user_id,
        "products": products
    }
    return render(request, "user_products.html", context)

def divs(request):
    cursor = connection.cursor()
    sql = "SELECT * FROM DIVISIONS ORDER BY div_id"
    cursor.execute(sql)
    result = cursor.fetchall()
    cursor.close()

    divs = []
    for r in result:
        divs.append({'div_id': r[0], 'div_name': r[1]})
    context = {
        "divs": divs,
        "user_id": request.session.get('user_id')
    }
    return render(request, 'divs.html', context)

def spec_div(request, div_id):
    cursor = connection.cursor()
    sql = "SELECT * FROM DIVISIONS ORDER BY div_id"
    cursor.execute(sql)
    result = cursor.fetchall()
    cursor.close()

    divs = []
    for r in result:
        id = r[0]
        div_name = r[1]
        if id == div_id:
            division_name = div_name
        divs.append({'div_id': id, 'div_name': div_name})

    cursor = connection.cursor()
    sql = "SELECT * FROM DISTRICTS WHERE div_id = %s ORDER BY dist_id"
    cursor.execute(sql, [div_id])
    result = cursor.fetchall()
    cursor.close()

    dists = []
    for r in result:
        dists.append({'dist_id': r[0], 'dist_name': r[1], 'div_id': r[2]})

    cursor = connection.cursor()
    sql = "SELECT * FROM AREAS WHERE dist_id IN (SELECT dist_id FROM DISTRICTS WHERE div_id = %s)"
    cursor.execute(sql, [div_id])
    result = cursor.fetchall()
    cursor.close()

    areas = []
    for r in result:
        areas.append({'area_id': r[0], 'name': r[1], 'dist_id': r[2]})

    context = {
        "divs": divs,
        "dists": dists,
        "div_id": div_id,
        "div_name": division_name,
        "areas": areas,
        "user_id": request.session.get('user_id')
    }
    return render(request, 'spec_div.html', context)

def spec_area(request, area_id):
    cursor = connection.cursor()
    sql = "SELECT AREA_NAME FROM AREAS WHERE AREA_ID = %s"
    cursor.execute(sql, [area_id])
    result = cursor.fetchall()
    cursor.close()
    area_name = result[0][0]

    cursor = connection.cursor()
    sql = "SELECT DIV_ID FROM DISTRICTS WHERE DIST_ID = (SELECT DIST_ID FROM AREAS WHERE AREA_ID = %s)"
    cursor.execute(sql, [area_id])
    result = cursor.fetchall()
    cursor.close()
    div_id = result[0][0]

    try:
        search = request.GET['search']
        cursor = connection.cursor()
        sql = "SELECT PRODUCT_ID, PRODUCT_NAME, AREA_ID FROM PRODUCT WHERE AREA_ID = %s AND UPPER(PRODUCT_NAME) LIKE %s"
        cursor.execute(sql, [area_id, '%' + search.upper() + '%'])
    except KeyError:
        cursor = connection.cursor()
        sql = "SELECT PRODUCT_ID, PRODUCT_NAME, AREA_ID FROM PRODUCT WHERE AREA_ID = %s"
        cursor.execute(sql, [area_id])
    result = cursor.fetchall()
    cursor.close()
    products = []
    for r in result:
        products.append({'product_id': r[0], 'product_name': r[1], 'area_id': r[2]})
    context = {
        "area_id": area_id,
        "div_id": div_id,
        "area_name": area_name,
        "products": products,
        "user_id": request.session.get('user_id')
    }

    return render(request, 'spec_area.html',context)

def ad_product(request):
    try:
        product_name = request.POST['product']
        price = request.POST['price']
        subcategory_name = request.POST['subcategory']
        category_name = request.POST['category']

        cursor = connection.cursor()
        sql = "SELECT CAT_ID FROM CATEGORIES WHERE UPPER(CAT_NAME) LIKE %s"
        cursor.execute(sql, [category_name.upper()])
        result = cursor.fetchall()
        cursor.close()

        if len(result) == 0:
            cursor = connection.cursor()
            sql = "SELECT cat_id_seq.nextval FROM DUAL"
            cursor.execute(sql)
            result = cursor.fetchall()
            cursor.close()
            cat_id = result[0][0]

            cursor = connection.cursor()
            insertsql = "INSERT INTO CATEGORIES(CAT_ID, CAT_NAME) VALUES (%s, %s)"
            cursor.execute(insertsql, [cat_id, category_name])
            connection.commit()
            cursor.close()

        cat_id = result[0][0]

        cursor = connection.cursor()
        sql = "SELECT SUBCAT_ID FROM SUB_CATEGORIES WHERE UPPER(SUBCAT_NAME) LIKE %s"
        cursor.execute(sql, [subcategory_name.upper()])
        result = cursor.fetchall()
        cursor.close()

        if len(result) == 0:
            cursor = connection.cursor()
            sql = "SELECT subcat_id_seq.nextval FROM DUAL"
            cursor.execute(sql)
            result = cursor.fetchall()
            cursor.close()
            subcat_id = result[0][0]

            cursor = connection.cursor()
            insertsql = "INSERT INTO SUB_CATEGORIES(SUBCAT_ID, SUBCAT_NAME, CATEGORY_ID) VALUES (%s, %s, %s)"
            cursor.execute(insertsql, [subcat_id, subcategory_name, cat_id])
            connection.commit()
            cursor.close()

        subcat_id = result[0][0]

        user_id = request.session.get('user_id', 0)
        cursor = connection.cursor()
        sql = "SELECT AREA_ID FROM PERSON WHERE ID = %s"
        cursor.execute(sql, [user_id])
        result = cursor.fetchall()
        cursor.close()
        area_id = result[0][0]

        cursor = connection.cursor()
        sql = "SELECT product_id_seq.nextval FROM DUAL"
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        product_id = result[0][0]

        try:
            stock = request.POST['stock']
            cursor = connection.cursor()
            insertsql = "INSERT INTO PRODUCT(PRODUCT_ID, PRICE, STOCK, ADVERTISER_ID, SUBCAT_ID, AREA_ID, PRODUCT_NAME) VALUES(%s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(insertsql, [product_id, price, stock, user_id, subcat_id, area_id, product_name])
            connection.commit()
            cursor.close()
        except KeyError:
            cursor = connection.cursor()
            insertsql = "INSERT INTO PRODUCT(PRODUCT_ID, PRICE, ADVERTISER_ID, SUBCAT_ID, AREA_ID, PRODUCT_NAME) VALUES(%s, %s, %s, %s, %s, %s)"
            cursor.execute(insertsql, [product_id, price, user_id, subcat_id, area_id, product_name])
            connection.commit()
            cursor.close()

        # cursor = connection.cursor()
        # insertsql = "INSERT INTO PRODUCT(PRODUCT_ID, PRICE, ADVERTISER_ID, SUBCAT_ID, AREA_ID, PRODUCT_NAME) VALUES(%s, %s, %s, %s, %s, %s)"
        # cursor.execute(insertsql, [product_id, price, user_id, subcat_id, area_id, product_name])
        # connection.commit()
        # cursor.close()

    except KeyError:
        return render(request, 'error.html', {"message": "Your product could not be added"})

    # try:
    #     stock = request.POST['stock']
    #     cursor = connection.cursor()
    #     updatesql = "UPDATE PRODUCT SET STOCK = NVL(%s, 1) WHERE PRODUCT_ID = %s"
    #     cursor.execute(updatesql, [stock, product_id])
    #     connection.commit()
    #     cursor.close()
    # except KeyError:
    #     pass

    try:
        imgpath = request.POST['imgpath']
        cursor = connection.cursor()
        updatesql = "UPDATE PRODUCT SET IMAGE = %s WHERE PRODUCT_ID = %s"
        cursor.execute(updatesql, [imgpath, product_id])
        connection.commit()
        cursor.close()
    except KeyError:
        pass

    try:
        desc = request.POST['desc']
        cursor = connection.cursor()
        updatesql = "UPDATE PRODUCT SET DESCRIPTION = %s WHERE PRODUCT_ID = %s"
        cursor.execute(updatesql, [desc, product_id])
        connection.commit()
        cursor.close()
    except KeyError:
        pass

    return HttpResponseRedirect(reverse("success"))

def success(request):
    return render(request, 'success.html')

def ad(request):
    return render(request, 'ad.html', {"user_id": request.session.get('user_id')})

def job_desc(request, job_id):
    user_id = request.session.get('user_id', 0)

    cursor = connection.cursor()
    sql = "SELECT JOB_ID, JOB_TITLE, DESCRIPTION, SALARY, REQUIREMENTS, COMPANY_ID, TYPE_ID FROM JOB WHERE JOB_ID = %s"
    cursor.execute(sql, [job_id])
    result = cursor.fetchall()
    cursor.close()
    r = result[0]

    cursor = connection.cursor()
    sql = "SELECT COMPANY_NAME, MANAGER_ID, C.AREA_ID, (SELECT AREA_NAME FROM AREAS A WHERE A.AREA_ID = C.AREA_ID) FROM COMPANY C WHERE COMPANY_ID = %s"
    cursor.execute(sql, [r[5]])
    result = cursor.fetchall()
    cursor.close()
    company_name = result[0][0]
    manager_id = result[0][1]
    area_id = result[0][2]
    area_name = result[0][3]

    cursor = connection.cursor()
    sql = "SELECT (SELECT DIST_NAME FROM DISTRICTS D WHERE D.DIST_ID = A.DIST_ID) FROM AREAS A WHERE A.AREA_ID = %s"
    cursor.execute(sql, [area_id])
    result = cursor.fetchall()
    cursor.close()
    dist_name = result[0][0]

    context = {
        "user_id": user_id,
        "company_name": company_name,
        "area_name": area_name,
        "dist_name": dist_name,
        "company_id": r[6],
        "job_id": r[0],
        "manager_id": manager_id,
        "job_title": r[1],
        "salary": r[3],
        "requirements": r[4] if r[4] else "NO SPECIFIC REQUIREMENT",
        "description": r[2] if r[2] else "Not provided",
        "type_id": r[5]
    }
    return render(request, 'job_desc.html', context )

def product_desc(request, product_id):
    user_id = request.session.get('user_id', 0)

    cursor = connection.cursor()
    sql = "SELECT CATEGORY_ID FROM SUB_CATEGORIES WHERE SUBCAT_ID = (SELECT SUBCAT_ID FROM PRODUCT WHERE PRODUCT_ID = %s)"
    cursor.execute(sql, [product_id])
    result = cursor.fetchall()
    cursor.close()
    cat_id = result[0][0]

    cursor = connection.cursor()
    sql = "SELECT PRODUCT_NAME, PRICE, STOCK, IMAGE, DESCRIPTION, SUBCAT_ID, ADVERTISER_ID FROM PRODUCT WHERE PRODUCT_ID = %s"
    cursor.execute(sql, [product_id])
    result = cursor.fetchall()
    cursor.close()
    r = result[0]

    cursor = connection.cursor()
    sql = "SELECT F_NAME || ' ' || L_NAME FROM PERSON WHERE ID = %s"
    cursor.execute(sql, [r[6]])
    result = cursor.fetchall()
    cursor.close()
    fullname = result[0][0]

    context = {
        "user_id": user_id,
        "fullname": fullname,
        "advertiser_id": r[6],
        "cat_id": cat_id,
        "product_id": product_id,
        "product_name": r[0],
        "price": r[1],
        "stock": r[2],
        "imgpath": r[3],
        "description": r[4] if r[4] is not None else "< Not provided by the advertiser >",
        "subcat_id": r[5]
    }
    return render(request, 'product_desc.html', context)

def chat(request, product_id):
    sender_id = request.session.get('user_id')

    cursor = connection.cursor()
    sql = "SELECT F_NAME || ' ' || L_NAME FROM PERSON WHERE ID = %s"
    cursor.execute(sql, [sender_id])
    result = cursor.fetchall()
    cursor.close()
    sender_name = result[0][0]

    cursor = connection.cursor()
    sql = "SELECT ADVERTISER_ID FROM PRODUCT WHERE PRODUCT_ID = %s"
    cursor.execute(sql, [product_id])
    result = cursor.fetchall()
    cursor.close()
    receiver_id = result[0][0]

    cursor = connection.cursor()
    sql = "SELECT F_NAME || ' ' || L_NAME FROM PERSON WHERE ID = %s"
    cursor.execute(sql, [receiver_id])
    result = cursor.fetchall()
    cursor.close()
    receiver_name = result[0][0]

    cursor = connection.cursor()
    # sql = "SELECT CHAT_ID FROM DISCUSSION WHERE SENDER_ID = %s AND RECEIVER_ID = %s AND PRODUCT_ID = %s"
    sql = "SELECT D.CHAT_ID FROM DISCUSSION D, CHAT C WHERE D.CHAT_ID = C.CHAT_ID AND ((SENDER_ID = %s AND RECEIVER_ID = %s) OR (SENDER_ID = %s AND RECEIVER_ID = %s)) AND PRODUCT_ID = %s ORDER BY C.CHAT_TIME"
    cursor.execute(sql, [sender_id, receiver_id, receiver_id, sender_id, product_id])
    chats = cursor.fetchall()
    cursor.close()
    messages = []
    if len(chats):
        for chat_id in chats:
            cursor = connection.cursor()
            sql = "SELECT MESSAGE_CONTENT, (SELECT SENDER_ID FROM DISCUSSION D WHERE D.CHAT_ID = C.CHAT_ID) FROM CHAT C WHERE C.CHAT_ID = %s"
            cursor.execute(sql, [chat_id[0]])
            message = cursor.fetchall()
            cursor.close()
            for m in message:
                messages.append({"message_content": m[0], "sender_id": m[1]})

    context = {
        "product_id": product_id,
        "sender_name": sender_name,
        "receiver_name": receiver_name,
        "messages": messages,
        "sender_id": sender_id
    }

    return render(request, 'chat.html', context)

def chat_with_contact(request, product_id, contact_id):
    user_id = request.session.get('user_id', 0)

    cursor = connection.cursor()
    sql = "SELECT F_NAME || ' ' || L_NAME FROM PERSON WHERE ID = %s"
    cursor.execute(sql, [contact_id])
    result = cursor.fetchall()
    cursor.close()
    sender_name = result[0][0]

    cursor = connection.cursor()
    sql = "SELECT F_NAME || ' ' || L_NAME FROM PERSON WHERE ID = %s"
    cursor.execute(sql, [user_id])
    result = cursor.fetchall()
    cursor.close()
    receiver_name = result[0][0]

    cursor = connection.cursor()
    sql = "SELECT D.CHAT_ID FROM DISCUSSION D, CHAT C WHERE D.CHAT_ID = C.CHAT_ID AND ((SENDER_ID = %s AND RECEIVER_ID = %s) OR (SENDER_ID = %s AND RECEIVER_ID = %s)) AND PRODUCT_ID = %s ORDER BY C.CHAT_TIME"
    cursor.execute(sql, [contact_id, user_id, user_id, contact_id, product_id])
    chats = cursor.fetchall()
    cursor.close()
    messages = []
    if len(chats):
        for chat_id in chats:
            cursor = connection.cursor()
            sql = "SELECT MESSAGE_CONTENT, (SELECT SENDER_ID FROM DISCUSSION D WHERE D.CHAT_ID = C.CHAT_ID) FROM CHAT C WHERE C.CHAT_ID = %s"
            cursor.execute(sql, [chat_id[0]])
            message = cursor.fetchall()
            cursor.close()
            for m in message:
                messages.append({"message_content": m[0], "sender_id": m[1]})

    context = {
        "product_id": product_id,
        "sender_name": sender_name,
        "receiver_name": receiver_name,
        "messages": messages,
        "contact_id": contact_id,
        "user_id": user_id
    }

    return render(request, 'chat_with_contact.html', context)

def ad_chat(request, product_id):
    user_id = request.session.get('user_id', 0)
    cursor = connection.cursor()
    sql = "SELECT chat_id_seq.nextval FROM DUAL"
    cursor.execute(sql)
    result = cursor.fetchall()
    cursor.close()
    chat_id = result[0][0]
    try:
        message_content  = request.POST['chat_box']
        cursor = connection.cursor()
        insertsql = "INSERT INTO CHAT(CHAT_ID, MESSAGE_CONTENT) VALUES (%s, %s)"
        cursor.execute(insertsql, [chat_id, message_content])
        connection.commit()
        cursor.close()

        cursor = connection.cursor()
        sql = "SELECT ADVERTISER_ID FROM PRODUCT WHERE PRODUCT_ID = %s"
        cursor.execute(sql, [product_id])
        result = cursor.fetchall()
        cursor.close()
        receiver_id = result[0][0]

        cursor = connection.cursor()
        insertsql = "INSERT INTO DISCUSSION VALUES (%s, %s, %s, %s)"
        cursor.execute(insertsql, [user_id, receiver_id, product_id, chat_id])
        connection.commit()
        cursor.close()
    except KeyError:
        return render(request, 'error.html', {"message": "Nothing to send"})

    return HttpResponseRedirect(reverse("chat", args = (product_id, )))

def contact_chat_action(request, product_id, contact_id):
    user_id = request.session.get('user_id', 0)
    cursor = connection.cursor()
    sql = "SELECT chat_id_seq.nextval FROM DUAL"
    cursor.execute(sql)
    result = cursor.fetchall()
    cursor.close()
    chat_id = result[0][0]
    try:
        message_content  = request.POST['chat_box']
        cursor = connection.cursor()
        insertsql = "INSERT INTO CHAT(CHAT_ID, MESSAGE_CONTENT) VALUES (%s, %s)"
        cursor.execute(insertsql, [chat_id, message_content])
        connection.commit()
        cursor.close()

        cursor = connection.cursor()
        insertsql = "INSERT INTO DISCUSSION VALUES (%s, %s, %s, %s)"
        cursor.execute(insertsql, [user_id, contact_id, product_id, chat_id])
        connection.commit()
        cursor.close()
    except KeyError:
        return render(request, 'error.html', {"message": "Nothing to send"})

    return HttpResponseRedirect(reverse("chat_with_contact", args = (product_id, contact_id)))

def applicants_list(request, job_id):
    user_id = request.session.get('user_id', 0)
    manager_id = -1
    cursor = connection.cursor()
    sql = "SELECT MANAGER_ID FROM COMPANY WHERE COMPANY_ID = (SELECT COMPANY_ID FROM JOB WHERE JOB_ID = %s)"
    cursor.execute(sql, [job_id])
    result = cursor.fetchall()
    cursor.close()
    if len(result):
        manager_id = result[0][0]

    if user_id != manager_id:
        return render(request, 'error.html', {"message": "You don't have access to browse this page"})

    cursor = connection.cursor()
    sql = "SELECT F_NAME || ' ' || L_NAME, ID FROM PERSON WHERE ID IN (SELECT APPLICANT_ID FROM JOB_APPLICATION WHERE JOB_ID = %s) "
    cursor.execute(sql, [job_id])
    result = cursor.fetchall()
    cursor.close()

    applicants = []
    for r in result:
        applicants.append({"applicant_name": r[0], "applicant_id": r[1]})
    context = {
        "applicants": applicants,
        "job_id": job_id
    }

    return render(request, "applicants_list.html",context)

def contacts_list(request, product_id):
    user_id = request.session.get('user_id', 0)
    cursor = connection.cursor()
    sql = "SELECT F_NAME || ' ' || L_NAME FULLNAME, ID FROM PERSON WHERE ID IN (SELECT SENDER_ID FROM DISCUSSION WHERE RECEIVER_ID = %s AND PRODUCT_ID = %s) ORDER BY FULLNAME"
    cursor.execute(sql, [user_id, product_id])
    result = cursor.fetchall()
    cursor.close()

    senders = []
    for r in result:
        senders.append({"name": r[0], "id": r[1]})
    context = {
        "senders": senders,
        "product_id": product_id
    }
    return render(request, "contacts_list.html", context)

def categories(request):
    cursor = connection.cursor()
    sql = "SELECT * FROM CATEGORIES ORDER BY CAT_ID"
    cursor.execute(sql)
    result = cursor.fetchall()
    cursor.close()

    categories = []
    for r in result:
        categories.append({'cat_id': r[0], 'cat_name': r[1], 'specifications': r[2] if r[2] is not None else 'No specifications provided'})

    context = {
        "user_id": request.session.get('user_id'),
        "categories": categories
    }

    return render(request, 'categories.html', context)

def spec_cat(request, cat_id):
    cursor = connection.cursor()
    sql = "SELECT CAT_NAME FROM CATEGORIES WHERE CAT_ID = %s"
    cursor.execute(sql, [cat_id])
    result = cursor.fetchall()
    cursor.close()
    cat_name = result[0][0]

    cursor = connection.cursor()
    sql = "SELECT * FROM SUB_CATEGORIES WHERE CATEGORY_ID = %s"
    cursor.execute(sql, [cat_id])
    result = cursor.fetchall()
    cursor.close()
    subcats = []
    for r in result:
        subcats.append({'subcat_id': r[0], 'subcat_name': r[1], 'properties': r[2], 'cat_id': r[3]})
    context = {
        "cat_id": cat_id,
        "cat_name": cat_name,
        "subcats": subcats,
        "user_id": request.session.get('user_id')
    }
    return render(request, 'spec_cat.html', context)

def subcat(request, cat_id, subcat_id):
    cursor = connection.cursor()
    sql = "SELECT CAT_NAME FROM CATEGORIES WHERE CAT_ID = %s"
    cursor.execute(sql, [cat_id])
    result = cursor.fetchall()
    cursor.close()
    cat_name = result[0][0]

    cursor = connection.cursor()
    sql = "SELECT SUBCAT_NAME FROM SUB_CATEGORIES WHERE SUBCAT_ID = %s"
    cursor.execute(sql, [subcat_id])
    result = cursor.fetchall()
    cursor.close()
    subcat_name = result[0][0]
    try:
        search = request.GET['search']
        cursor = connection.cursor()
        sql = "SELECT PRODUCT_ID, PRODUCT_NAME FROM PRODUCT WHERE SUBCAT_ID = %s AND UPPER(PRODUCT_NAME) LIKE %s"
        cursor.execute(sql, [subcat_id, '%' + search.upper() + '%'])
    except KeyError:
        cursor = connection.cursor()
        sql = "SELECT PRODUCT_ID, PRODUCT_NAME FROM PRODUCT WHERE SUBCAT_ID = %s"
        cursor.execute(sql, [subcat_id])
    result = cursor.fetchall()
    cursor.close()
    products = []
    for r in result:
        products.append({'product_id': r[0], 'product_name': r[1]})
    context = {
        "cat_id": cat_id,
        "cat_name": cat_name,
        "subcat_name": subcat_name,
        "products": products,
        "user_id": request.session.get('user_id')
    }
    return render(request, 'subcat.html', context)

def signup(request):
    cursor = connection.cursor()
    sql = "SELECT * FROM DIVISIONS ORDER BY div_id"
    cursor.execute(sql)
    result = cursor.fetchall()
    cursor.close()
    divs = []
    for r in result:
        divs.append({'div_id': r[0], 'div_name': r[1]})

    cursor = connection.cursor()
    sql = "SELECT * FROM DISTRICTS ORDER BY DIST_NAME"
    cursor.execute(sql)
    result = cursor.fetchall()
    cursor.close()
    dists = []
    for r in result:
        dists.append({'dist_id': r[0], 'dist_name': r[1], 'div_id': r[2]})

    context = {
        "divs": divs,
        "dists": dists
    }
    return render(request, 'signup.html', context)

def new_user(request):
    try:
        f_name = request.POST['f_name']
        l_name = request.POST['l_name']
        phone = request.POST['phone']
        password = request.POST['password']
        area = request.POST['area']
        div_id = request.POST['divid']
        dist_id = request.POST['distid']

        # cursor = connection.cursor()
        # sql = "SELECT AREA_ID FROM AREAS WHERE AREA_NAME = %s AND DIST_ID = %s"
        # cursor.execute(sql, [area, dist_id])
        # result = cursor.fetchall()
        # cursor.close()

        cursor = connection.cursor()
        sql = "SELECT NEW_AREA_ID (%s, %s) FROM DUAL"  # using function NEW_AREA_ID
        cursor.execute(sql, [area, dist_id])
        result = cursor.fetchall()
        cursor.close()

        area_id = result[0][0]

        if area_id == -1:
            cursor = connection.cursor()
            sql = "SELECT area_id_seq.nextval FROM DUAL"
            cursor.execute(sql)
            result = cursor.fetchall()
            cursor.close()
            area_id = result[0][0]

            cursor = connection.cursor()
            # insertsql = "INSERT INTO AREAS VALUES ((SELECT COUNT(AREA_ID)+1 FROM AREAS), %s, %s)"
            insertsql = "INSERT INTO AREAS VALUES (%s, INITCAP(%s), %s)"
            cursor.execute(insertsql, [area_id, area, dist_id])
            connection.commit()
            cursor.close()

        area_id = result[0][0]

        hash_obj = hashlib.sha1(password.encode())
        password = hash_obj.hexdigest()

        cursor = connection.cursor()
        sql = "SELECT person_id_seq.nextval FROM DUAL"
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        person_id = result[0][0]

        cursor = connection.cursor()
        insertsql = "INSERT INTO PERSON(ID, F_NAME, L_NAME, AREA_ID, PHONE_NO, PASSWORD) VALUES (%s, %s, %s, %s, %s, %s)"
        cursor.execute(insertsql, [person_id, f_name, l_name, area_id, phone, password])
        connection.commit()
        cursor.close()

        request.session['user_id'] = person_id
    except KeyError:
        return render(request, 'error.html', {"message": "Signup failed. Please select your area division and district"})

    try:
        street = request.POST['street']
        cursor = connection.cursor()
        updatesql = "UPDATE PERSON SET STREET = %s WHERE ID = %s"
        cursor.execute(updatesql, [street, person_id])
        connection.commit()
        cursor.close()
    except KeyError:
        pass

    try:
        zip = request.POST['zip']
        cursor = connection.cursor()
        updatesql = "UPDATE PERSON SET ZIP_CODE = %s WHERE ID = %s"
        cursor.execute(updatesql, [zip, person_id])
        connection.commit()
        cursor.close()
    except KeyError:
        pass

    try:
        house = request.POST['house']
        cursor = connection.cursor()
        updatesql = "UPDATE PERSON SET HOUSE = %s WHERE ID = %s"
        cursor.execute(updatesql, [house, person_id])
        connection.commit()
        cursor.close()
    except KeyError:
        pass

    return HttpResponseRedirect(reverse("index"))

def user_login(request):
    try:
        username = request.POST['username']
        password = request.POST['password']
        hash_obj = hashlib.sha1(password.encode())
        password = hash_obj.hexdigest()
        cursor = connection.cursor()
        sql = "SELECT ID FROM PERSON WHERE F_NAME = %s AND PASSWORD = %s"
        cursor.execute(sql, [username, password])
        result = cursor.fetchall()
        cursor.close()
        if len(result) == 0:
            return render(request, 'login.html', {"cred": -1})

    except KeyError:
        return render(request, 'login.html', {"cred": 1})
    request.session['user_id'] = result[0][0]
    return HttpResponseRedirect(reverse('index'))

def user_logout(request):
    request.session['user_id'] = 0
    return HttpResponseRedirect(reverse("index"))

def register_company(request):
    cursor = connection.cursor()
    sql = "SELECT * FROM DIVISIONS ORDER BY div_id"
    cursor.execute(sql)
    result = cursor.fetchall()
    cursor.close()
    divs = []
    for r in result:
        divs.append({'div_id': r[0], 'div_name': r[1]})

    cursor = connection.cursor()
    sql = "SELECT * FROM DISTRICTS ORDER BY DIST_NAME"
    cursor.execute(sql)
    result = cursor.fetchall()
    cursor.close()
    dists = []
    for r in result:
        dists.append({'dist_id': r[0], 'dist_name': r[1], 'div_id': r[2]})

    context = {
        "divs": divs,
        "dists": dists
    }
    return render(request, 'register_company.html', context)

def job_types(request):
    cursor = connection.cursor()
    sql = "SELECT * FROM JOB_TYPE ORDER BY TITLE"
    cursor.execute(sql)
    result = cursor.fetchall()
    cursor.close()

    types = []
    for r in result:
        types.append({'type_id': r[0], 'title': r[1]})

    context = {
        "user_id": request.session.get('user_id'),
        "types": types
    }

    return render(request, 'job_types.html', context)

def job_list(request, type_id):
    cursor = connection.cursor()
    sql = "SELECT JOB_ID, JOB_TITLE, (SELECT COMPANY_NAME FROM COMPANY C WHERE C.COMPANY_ID = J.COMPANY_ID) FROM JOB J WHERE J.TYPE_ID = %s ORDER BY JOB_ID"
    cursor.execute(sql, [type_id])
    result = cursor.fetchall()
    cursor.close()

    job_list = []
    for r in result:
        job_list.append({'job_id': r[0], 'job_title': r[1], 'comp_name': r[2]})
    context = {
        "job_list": job_list,
        "user_id": request.session.get('user_id')
    }
    return render(request, 'job_list.html', context)

def add_company(request):
    user_id = request.session.get('user_id', 0)
    try:
        comp_name = request.POST['comp_name']
        area = request.POST['area']
        div_id = request.POST['divid']
        dist_id = request.POST['distid']

        # cursor = connection.cursor()
        # sql = "SELECT AREA_ID FROM AREAS WHERE AREA_NAME = %s AND DIST_ID = %s"
        # cursor.execute(sql, [area, dist_id])
        # result = cursor.fetchall()
        # cursor.close()

        cursor = connection.cursor()
        sql = "SELECT NEW_AREA_ID (%s, %s) FROM DUAL"  # using function NEW_AREA_ID
        cursor.execute(sql, [area, dist_id])
        result = cursor.fetchall()
        cursor.close()

        area_id = result[0][0]

        if area_id == -1:
            cursor = connection.cursor()
            sql = "SELECT area_id_seq.nextval FROM DUAL"
            cursor.execute(sql)
            result = cursor.fetchall()
            cursor.close()
            area_id = result[0][0]

            cursor = connection.cursor()
            # insertsql = "INSERT INTO AREAS VALUES ((SELECT COUNT(AREA_ID)+1 FROM AREAS), %s, %s)"
            insertsql = "INSERT INTO AREAS VALUES (%s, INITCAP(%s), %s)"
            cursor.execute(insertsql, [area_id, area, dist_id])
            connection.commit()
            cursor.close()

        area_id = result[0][0]

        cursor = connection.cursor()
        sql = "SELECT comp_id_seq.nextval FROM DUAL"
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        comp_id = result[0][0]

        cursor = connection.cursor()
        insertsql = "INSERT INTO COMPANY VALUES (%s, %s, %s, %s)"
        cursor.execute(insertsql, [comp_id, comp_name, area_id, user_id])
        connection.commit()
        cursor.close()

    except KeyError:
        return render(request, 'error.html', {"message": "Registration failed. Please provide all the necessary details"})

    return HttpResponseRedirect(reverse("offered_jobs", args = (comp_id, )))

def offered_jobs(request, comp_id):
    user_id = request.session.get('user_id', 0)
    cursor = connection.cursor()
    sql = "SELECT MANAGER_ID FROM COMPANY WHERE COMPANY_ID = %s"
    cursor.execute(sql, [comp_id])
    result = cursor.fetchall()
    cursor.close()
    if len(result):
        manager_id = result[0][0]
    if user_id != manager_id:
        return render(request, 'error.html', {"message": "You don't have access to browse this page"})
    cursor = connection.cursor()
    sql = "SELECT COMPANY_NAME FROM COMPANY WHERE COMPANY_ID = %s"
    cursor.execute(sql, [comp_id])
    result = cursor.fetchall()
    cursor.close()
    comp_name = result[0][0]

    cursor = connection.cursor()
    sql = "SELECT JOB_ID, JOB_TITLE, COMPANY_ID FROM JOB WHERE COMPANY_ID = %s"
    cursor.execute(sql, [comp_id])
    result = cursor.fetchall()
    cursor.close()
    jobs = []
    for r in result:
        jobs.append({'job_id': r[0], 'job_title': r[1], 'comp_id': r[2]})
    context = {
        "comp_id": comp_id,
        "comp_name": comp_name,
        "jobs": jobs,
        "user_id": request.session.get('user_id')
    }
    return render(request, 'offered_jobs.html', context)

def add_job(request, comp_id):
    try:
        job_title = request.POST['job_title']
        salary = request.POST['salary']
        job_type = request.POST['job_type']

        cursor = connection.cursor()
        sql = "SELECT TYPE_ID FROM JOB_TYPE WHERE TITLE = %s"
        cursor.execute(sql, [job_type])
        result = cursor.fetchall()
        cursor.close()
        if len(result) == 0:
            cursor = connection.cursor()
            sql = "SELECT type_id_seq.NEXTVAL FROM DUAL"
            cursor.execute(sql)
            result = cursor.fetchall()
            cursor.close()
            type_id = result[0][0]

            cursor = connection.cursor()
            insertsql = "INSERT INTO JOB_TYPE VALUES (%s, %s)"
            cursor.execute(insertsql, [type_id, job_type])
            connection.commit()
            cursor.close()

        type_id = result[0][0]

        cursor = connection.cursor()
        sql = "SELECT job_id_seq.NEXTVAL FROM DUAL"
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        job_id = result[0][0]

        cursor = connection.cursor()
        sql = "SELECT AREA_ID FROM COMPANY WHERE COMPANY_ID = %s"
        cursor.execute(sql, [comp_id])
        result = cursor.fetchall()
        cursor.close()
        area_id = result[0][0]

        cursor = connection.cursor()
        insertsql = "INSERT INTO JOB(JOB_ID, JOB_TITLE, SALARY, TYPE_ID, AREA_ID, COMPANY_ID) VALUES (%s, %s, %s, %s, %s, %s)"
        cursor.execute(insertsql, [job_id, job_title, salary, type_id, area_id, comp_id])
        connection.commit()
        cursor.close()

    except KeyError:
        return render(request, 'error.html', {"message": "The job couldn't be added"})

    try:
        desc = request.POST['desc']
        cursor = connection.cursor()
        updatesql = "UPDATE JOB SET DESCRIPTION = %s WHERE JOB_ID = %s"
        cursor.execute(updatesql, [desc, job_id])
        connection.commit()
        cursor.close()
    except KeyError:
        pass

    try:
        req = request.POST['req']
        cursor = connection.cursor()
        updatesql = "UPDATE JOB SET REQUIREMENTS = %s WHERE JOB_ID = %s"
        cursor.execute(updatesql, [req, job_id])
        connection.commit()
        cursor.close()
    except KeyError:
        pass

    return HttpResponseRedirect(reverse("offered_jobs", args = (comp_id, )))
