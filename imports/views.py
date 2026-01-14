from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import ImportForm
from .models import ImportJob
from .utils import process_agent_import, process_call_import
from django.contrib import messages
import os
from django.conf import settings

@login_required
def import_data(request):
    if request.method == 'POST':
        form = ImportForm(request.POST, request.FILES)
        if form.is_valid():
            job = form.save(commit=False)
            job.user = request.user
            # job.tenant = request.user.tenant # Removed
            job.save()
            
            # Process immediately (should be async in prod)
            file_path = job.file.path
            if job.import_type == 'agents':
                logs = process_agent_import(file_path)
            else:
                logs = process_call_import(file_path)
                
            job.status = 'completed'
            job.logs = "\n".join(logs)
            job.save()
            
            # Post-process: Aggregate if calls were imported
            if job.import_type == 'calls':
                try:
                    from calls.utils import aggregate_actuals
                    aggregate_actuals()
                    job.logs += "\nSuccessfully aggregated call volumes."
                    job.save()
                except Exception as e:
                    job.logs += f"\nError in aggregation: {e}"
                    job.save()
            
            messages.success(request, "Import completed.")
            return redirect('import_data')
    else:
        form = ImportForm()
        
    jobs = ImportJob.objects.all().order_by('-created_at')
    return render(request, 'import.html', {'form': form, 'jobs': jobs})

@login_required
def download_sample_csv(request, type):
    import csv
    from django.http import HttpResponse

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="sample_{type}.csv"'
    
    writer = csv.writer(response)
    
    if type == 'agents':
        writer.writerow(['agent_id', 'firstname', 'lastname', 'email', 'skills', 'team', 'employee_id'])
        writer.writerow(['ahmet.yilmaz', 'Ahmet', 'Yılmaz', 'ahmet@example.com', 'Satış:5|İkna:4', 'Satış', 'EMP1001'])
    elif type == 'calls':
        writer.writerow(['call_id', 'timestamp', 'duration', 'agent', 'queue'])
        writer.writerow(['unique-id-1', '2026-01-01 09:30:00', '120', 'ahmet.yilmaz', 'Satış Hattı'])
        
    return response
