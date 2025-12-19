import enum


class TicketStatus(enum.Enum):
    """
    ENUM для перечисления статуса заявки
    """
    new = 'new'
    in_progress = 'in_progress'
    canceled = 'cancelled'
    completed = 'completed'
