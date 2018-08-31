from django.shortcuts import render, HttpResponse, redirect, HttpResponseRedirect, get_object_or_404
from fanyi import models as layout
from rbac import models
from wiki import models
from django.db.models import Q
from utils import pagination
from utils import resizeImg
import json, time, markdown2, os
from django.views.decorators.csrf import csrf_exempt
from .forms import EditorTestForm
from django.http import JsonResponse


# Create your views here.

def auth(func):
    def inner(request, *args, **kwargs):
        # login_url = "https://login.sogou-inc.com/?appid=1162&sso_redirect=http://frontqa.web.sjs.ted/&targetUrl="
        # try:
        #     user_id = request.COOKIES.get('uid')
        #     if not user_id:
        #         return redirect(login_url)
        # except:
        #     return redirect(login_url)
        # v = request.COOKIES.get('username111')
        return func(request, *args, **kwargs)

    return inner


# wiki detail
@auth
def wiki_detail(request, task_id):
    # user_id = 'zhangjingjun'
    user_id = request.COOKIES.get('uid')
    try:
        req_lst = layout.ReqInfo.objects.filter(user_fk_id=user_id)
        app_id_lst = list()

        wikidetail = models.Wikistore.objects.filter(id=task_id).values()
        format_md = markdown2.markdown(wikidetail[0]['wikicontent'])

        wikitags = models.Wikistore.objects.filter(id=task_id).values('wikitag')
        taglist = list()
        for item in wikitags:
            if '--' in item['wikitag']:
                tagsp = item['wikitag'].split('--')
                taglist += tagsp
            else:
                taglist.append(item['wikitag'])
        taglist = list(set(taglist))

    except Exception as e:
        print(e)
        pass
    return render(request, 'wiki/wiki_detail.html',
                  {'user_id': user_id,
                   'req_lst': req_lst,
                   'wikidetail': wikidetail, 'format_md': format_md, 'taglist': taglist})


# del wiki
@csrf_exempt
@auth
def del_wiki(request):
    # user_id = 'zhangjingjun'
    ret = {'status': True, 'error': None, 'data': None}
    req_id = request.POST.get('line_id')
    try:
        # models.Wikistore.objects.filter(id=req_id).update(status=2)
        models.Wikistore.objects.filter(id=req_id).delete()
    except Exception as e:
        ret['status'] = False
        ret['error'] = "Error:" + str(e)
    return HttpResponse(json.dumps(ret))


# wiki list
@auth
def wiki_list(request, page_id='1'):
    tag = request.GET.get('tag')
    status = request.GET.get('status')
    user_id = 'zhangjingjun'
    if page_id == '':
        page_id = 1
    try:
        req_lst = layout.ReqInfo.objects.filter(user_fk_id=user_id)

        if status == '0':
            wikilist = models.Wikistore.objects.filter(user=user_id, status=0).order_by('update_time')[::-1]
        elif tag is None or tag == 'all':
            wikilist = models.Wikistore.objects.exclude(status=2).filter(Q(status=1) | Q(user=user_id)).order_by(
                'update_time')[::-1]
        else:
            wikilist = models.Wikistore.objects.exclude(status=2).filter(
                Q(wikitag__icontains=tag, status=1) | Q(user=user_id, wikitag__icontains=tag)).order_by('update_time')[
                       ::-1]
        current_page = page_id
        current_page = int(current_page)
        page_obj = pagination.Page(current_page, len(wikilist), 10, 9)
        data = wikilist[page_obj.start:page_obj.end]
        page_str = page_obj.page_str("wiki/wiki_list")
        wikitags = models.Wikistore.objects.exclude(status=2).filter(Q(status=1) | Q(user=user_id)).values('wikitag')
        taglist = list()
        for item in wikitags:
            if '--' in item['wikitag']:
                tagsp = item['wikitag'].split('--')
                taglist += tagsp
            else:
                taglist.append(item['wikitag'])
        taglist = list(set(taglist))

    except Exception as e:
        print(e)
        pass

    return render(request, 'wiki/wiki_list.html',
                  {'user_id': user_id,
                   'req_lst': req_lst,
                   'li': data, 'page_str': page_str, 'taglist': taglist})


def wiki(request, page_id='1'):
    if page_id == '':
        page_id = 1
    if request.method == "GET":
        # form = EditorTestForm(instance=b)
        tag = request.GET.get('tag')
        category = request.GET.get('category')

        if tag and category == None:
            data = models.Wikistore.objects.filter(wikitag=tag)

            return render(request, 'wiki/wiki.html',
                          {'form': data})
        elif tag == None and category:
            data = models.Wikistore.objects.filter(category=category)

            return render(request, 'wiki/wiki.html',
                          {'form': data})
        elif tag == None and category == None:
            wiki_list = models.Wikistore.objects.all()
            category_list = models.Wikistore.objects.values('category').distinct()
            tag_list = models.Wikistore.objects.values('wikitag').distinct()

            current_page = int(page_id)
            page_obj = pagination.Page(current_page, len(wiki_list), 10, 9)
            data = wiki_list[page_obj.start:page_obj.end]
            page_str = page_obj.page_str('/wiki/wiki')
            return render(request, 'wiki/wiki.html',
                          {'form': data, 'page_str': page_str, 'category_list': category_list, 'tag_list': tag_list})


# save blog
@csrf_exempt
@auth
def save_blog(request):
    user_id = 'zhangjingjun'
    # user_id = request.COOKIES.get('uid')
    ret = {'status': True, 'error': None, 'data': None}
    title = request.POST.get('title')
    # summary=request.POST.get('summary')
    content = request.POST.get('content')
    tags = request.POST.get('wikitag')
    flag = request.POST.get('flag')
    try:
        if flag == 'add':
            models.Wikistore.objects.create(create_time=get_now_time(), user=user_id, update_user=user_id,
                                            update_time=get_now_time(), wikititle=title, wikicontent=content,
                                            wikitag=tags, status=1)
        elif flag == 'update':
            id = request.POST.get('edit_id')
            models.Wikistore.objects.filter(id=id).update(update_user=user_id,
                                                          update_time=get_now_time(), wikititle=title,
                                                          wikicontent=content, wikitag=tags, status=1)
        elif flag == 'draft':
            models.Wikistore.objects.create(create_time=get_now_time(), user=user_id, update_user=user_id,
                                            update_time=get_now_time(), wikititle=title,
                                            wikicontent=content, wikitag=tags, status=0)
    except Exception as e:
        ret['status'] = False
        ret['error'] = 'error:' + str(e)
    return HttpResponse(json.dumps(ret))


# edit blog
@auth
def edit_blog(request):
    user_id = request.COOKIES.get('uid')
    edit_id = request.GET.get('id')
    try:
        req_lst = layout.ReqInfo.objects.filter(user_fk_id=user_id)

        edit_content = models.Wikistore.objects.filter(id=edit_id).values()

        wikitags = models.Wikistore.objects.exclude(status=2).filter(Q(status=1) | Q(user=user_id)).values('wikitag')
        taglist = list()
        for item in wikitags:
            if '--' in item['wikitag']:
                tagsp = item['wikitag'].split('--')
                taglist += tagsp
            else:
                taglist.append(item['wikitag'])
        taglist = list(set(taglist))
    except Exception as e:
        print(e)
        pass

    return render(request, 'wiki/wiki_edit_blog.html',
                  {'user_id': user_id,
                   'req_lst': req_lst,
                   'edit_content': edit_content, 'taglist': taglist})


def edit_wiki(request):
    user_id = 'gongyanli'
    # user_id=request.COOKIES.get('uid')
    edit_id = request.GET.get('id')
    # b = models.UserInfo.objects.filter(user_fk_id=user_id)
    edit_content = models.Wikistore.objects.get(id=edit_id)

    if request.method == "GET":
        form = EditorTestForm(instance=edit_content)
        return render(request, 'wiki/wiki_add.html', {'form': form})
    if request.method == "POST":
        form = EditorTestForm(request.POST, instance=edit_content)
        if form.is_valid():
            wiki = form.save(commit=False)
            # form.wikititle = request.POST.get('title')
            wiki.update_time = get_now_time()
            wiki.update_user = user_id
            wiki.save()
            return HttpResponseRedirect('wiki/')

            # return JsonResponse(dict(success=1, message="submit success!"))
        else:
            return JsonResponse(dict(success=0, message="submit error"))


# add blog
# @csrf_exempt
# @auth
# def add_wiki(request):
#     user_id = 'zhangjingjun'
#     # user_id = request.COOKIES.get('uid')
#     try:
#         req_lst = layout.ReqInfo.objects.filter(user_fk_id=user_id)
#
#         wikitags = models.Wikistore.objects.exclude(status=2).filter(Q(status=1) | Q(user=user_id)).values('wikitag')
#         taglist = list()
#         for item in wikitags:
#             if '--' in item['wikitag']:
#                 tagsp = item['wikitag'].split('--')
#                 taglist += tagsp
#             else:
#                 taglist.append(item['wikitag'])
#         taglist = list(set(taglist))
#     except Exception as e:
#         print(e)
#         pass
#
#     return render(request, 'wiki/wiki_add_blog.html',
#                   {'user_id': user_id,
#                    'req_lst': req_lst,
#                    'taglist': taglist})


def add_wiki(request):
    user_id = 'gongyanli'
    # user_id = request.COOKIES.get('uid')
    if request.method == "POST":

        obj = models.Wikistore.objects.create(user=user_id, create_time=get_now_time(), update_time=get_now_time())
        form = EditorTestForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('wiki/')
            # return render(request, 'wiki/wiki_list.html', {'form': form})
            # return JsonResponse(dict(success=1, message="submit success!"))
        else:
            return JsonResponse(dict(success=0, message="submit error"))
    else:
        form = EditorTestForm()
        return render(request, 'wiki/wiki_add.html', {'form': form})


def get_now_time():
    timeArray = time.localtime()
    return time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
