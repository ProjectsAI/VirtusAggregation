from src.enums import ProfileType
from src.profile import Profile


class Wind(Profile):

    def __init__(self, l, scale_factor=10, min_shift=10, max_shift=10, total_shift=0, cost_min=0, cost_max=0,
                 timestamps=96):
        super().__init__([x * scale_factor if x < 0 else x for x in l], ProfileType.WIND, cost_min, cost_max,
                         timestamps)
        # Using profile percentage for min_shift and max_shift allows the shift only if the profile is positive
        self.scale_factor = scale_factor
        self.min_shift = self.setup_array_for_property([x * (min_shift / 100) * self.scale_factor for x in l])
        self.max_shift = self.setup_array_for_property([-x * (max_shift / 100) * self.scale_factor for x in l])

        self.min_flex = self.setup_array_for_property(
            [(x * self.scale_factor - (x * self.scale_factor * (min_shift / 100))) for x in l])
        self.max_flex = self.setup_array_for_property(
            [(x * self.scale_factor + (x * self.scale_factor * (max_shift / 100))) for x in l])
        self.total_shift = total_shift

    def get_flexibility(self, type='minimized'):
        if type == 'minimized':
            return self.max_flex
        if type == 'maximized':
            return self.min_flex
