from django.shortcuts import render

def home_view(request):
    return render(request,'home.html')

def search_view(request):
    if request.method == 'POST':
            searched = request.POST['searched']        
            # recipes = Recipe.objects.filter(name__contains=searched) # Recipe는 임시 모델의 클래스 이름
            # return render(request, 'searched.html', {'searched': searched, 'recipes': recipes})
            return render(request, 'search.html', {'searched': searched})
    else:
            return render(request, 'search.html', {})

def corp_detail_view(request):
    return render(request,'corp_detail.html')