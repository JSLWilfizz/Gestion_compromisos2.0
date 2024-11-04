# /validators/reunion_validator.py

class ReunionValidator:
    @staticmethod
    def validate_first_step(form):
        is_valid = True
        if not form.origen.validate(form):
            is_valid = False
        if not form.area.validate(form):
            is_valid = False
        return is_valid
