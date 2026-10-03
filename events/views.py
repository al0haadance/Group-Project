import calendar as pycalendar
from datetime import date

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from accounts.permissions import AdminRequiredMixin
from .models import Event

MONTH_NAMES_UK = [
    '', 'Січень', 'Лютий', 'Березень', 'Квітень', 'Травень', 'Червень',
    'Липень', 'Серпень', 'Вересень', 'Жовтень', 'Листопад', 'Грудень',
]


class EventCalendarView(ListView):
    """Календар подій у вигляді сітки на місяць. Додавати/редагувати/видаляти може лише admin."""
    model = Event
    template_name = 'events/calendar.html'
    context_object_name = 'events'

    def get_year_month(self):
        today = date.today()
        year = int(self.request.GET.get('year', today.year))
        month = int(self.request.GET.get('month', today.month))
        if month < 1:
            month, year = 12, year - 1
        elif month > 12:
            month, year = 1, year + 1
        return year, month

    def get_queryset(self):
        year, month = self.get_year_month()
        return Event.objects.filter(date__year=year, date__month=month).order_by('date')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        year, month = self.get_year_month()

        cal = pycalendar.Calendar(firstweekday=0)
        month_days = cal.itermonthdates(year, month)

        events_by_day = {}
        for event in self.get_queryset():
            events_by_day.setdefault(event.date.day, []).append(event)

        weeks, week = [], []
        for day in month_days:
            in_month = day.month == month
            week.append({
                'date': day,
                'in_month': in_month,
                'is_today': day == date.today(),
                'events': events_by_day.get(day.day, []) if in_month else [],
            })
            if len(week) == 7:
                weeks.append(week)
                week = []

        prev_month = month - 1 or 12
        prev_year = year - 1 if month == 1 else year
        next_month = month + 1 if month < 12 else 1
        next_year = year + 1 if month == 12 else year

        ctx.update({
            'weeks': weeks,
            'month_name': MONTH_NAMES_UK[month],
            'year': year, 'month': month,
            'prev_year': prev_year, 'prev_month': prev_month,
            'next_year': next_year, 'next_month': next_month,
            'can_manage': self.request.user.is_authenticated and self.request.user.is_admin_role,
        })
        return ctx


class EventListView(ListView):
    model = Event
    template_name = 'events/list.html'
    context_object_name = 'events'
    paginate_by = 15

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        now = timezone.now()
        ctx['upcoming'] = self.get_queryset().filter(date__gte=now)
        ctx['past'] = self.get_queryset().filter(date__lt=now)
        return ctx


class EventDetailView(DetailView):
    model = Event
    template_name = 'events/detail.html'
    context_object_name = 'event'


class EventCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Event
    fields = ['title', 'description', 'date', 'location']
    template_name = 'events/form.html'
    success_url = reverse_lazy('events:list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class EventUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Event
    fields = ['title', 'description', 'date', 'location']
    template_name = 'events/form.html'
    success_url = reverse_lazy('events:list')


class EventDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Event
    template_name = 'events/confirm_delete.html'
    success_url = reverse_lazy('events:list')
