from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from ..forms import ProfileCompletionForm, ProfileEditForm


# Profile Completion
@login_required
def complete_profile(request):
    if request.user.is_profile_complete:
        if request.user.role == 'artist':
            return redirect('artist_dashboard')
        else:
            return redirect('client_dashboard')

    if request.method == 'POST':
        form = ProfileCompletionForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_profile_complete = True
            user.save()
            if user.role == 'artist':
                return redirect('artist_dashboard')
            else:
                return redirect('client_dashboard')
    else:
        form = ProfileCompletionForm(instance=request.user)

    return render(request, 'profile/complete_profile.html', {'form': form})



@login_required
def edit_profile(request):
    user = request.user
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('artist_dashboard' if user.role=='artist' else 'client_dashboard')
    else:
        form = ProfileEditForm(instance=user)

    return render(request, 'profile/edit_profile.html', {'form': form})
