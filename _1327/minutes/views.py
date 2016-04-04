from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from _1327.minutes.models import MinutesDocument


@login_required
def list(request):
	years = {}
	minutes = MinutesDocument.objects.order_by('-date')
	for m in minutes:
		if not request.user.has_perm(m, MinutesDocument.get_view_permission()):
			continue

		if m.date.year not in years:
			years[m.date.year] = []
		years[m.date.year].append(m)
	new_years = [{'year': year, 'minutes': minutes} for (year, minutes) in years.items()]
	new_years = sorted(new_years, key=lambda x: x['year'], reverse=True)
	return render(request, "minutes_list.html", {
		'years': new_years,
	})
