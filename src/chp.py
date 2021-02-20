from src.enums import ProfileType
from src.profile import Profile


class CHP(Profile):

    def __init__(self, l, allowed_t: [], min_shift, max_shift, cost_min=0, cost_max=0, timestamps=96):
        super().__init__(l, ProfileType.CHP, cost_min, cost_max, timestamps)
        self.allowed_t = [1 if i in allowed_t else 0 for i in range(self.timestamps)]
        self.min_shift = self.setup_array_for_property(min_shift)
        self.max_shift = self.setup_array_for_property(max_shift)

    def get_flexibility(self, type='minimized'):
        if type == 'minimized':
            return self.min_shift * self.allowed_t
        if type == 'maximized':
            return self.max_shift * self.allowed_t

    def get_min_flexibility(self):
        return self.min_shift * self.allowed_t

    def get_max_flexibility(self):
        return self.max_shift * self.allowed_t
