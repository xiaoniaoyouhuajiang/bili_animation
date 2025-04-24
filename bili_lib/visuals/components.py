from manim import *

BLUE_COLOR = BLUE_D # 使用 Manim 预设的深蓝色

class OSThreadBox(VGroup):
    """Represents the OS Thread container."""
    def __init__(self, width=14.5, height=6.5, label="OS Thread", **kwargs):
        super().__init__(**kwargs)
        self.box = Rectangle(width=width, height=height, color=BLUE_COLOR, stroke_width=2)
        self.label = Text(label, font_size=24).next_to(self.box, UP, buff=0.1)
        self.add(self.box, self.label)

class CPUBox(VGroup):
    """Represents the CPU with key registers."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.box = Rectangle(width=4.5, height=3.5, color=BLUE_COLOR, stroke_width=2)
        self.label = Text("CPU", font_size=20).next_to(self.box, UP, buff=0.1)

        # Register placeholders (simplified)
        self.registers = VGroup(
            Text("rsp: 0x...", font_size=32),
            Text("rip: 0x...", font_size=32),
            Text("rbx: 0x...", font_size=32),
            Text("rbp: 0x...", font_size=32),
            Text("r12: 0x...", font_size=32),
            # Add r13-r15 if needed
        ).arrange(DOWN, buff=0.1, aligned_edge=LEFT).scale(0.8).move_to(self.box.get_center())

        self.add(self.box, self.label, self.registers)

    def update_registers(self, reg_values: dict):
        """Updates the text of the register labels."""
        animations = []
        for i, reg_text_mobject in enumerate(self.registers):
            reg_name = reg_text_mobject.text.split(":")[0]
            if reg_name in reg_values:
                new_text = f"{reg_name}: {reg_values[reg_name]}"
                # Create a new Text mobject for smooth transform
                new_label = Text(new_text, font_size=reg_text_mobject.font_size, weight=BOLD)
                new_label.move_to(reg_text_mobject)
                new_label.align_to(reg_text_mobject, LEFT)
                animations.append(Transform(reg_text_mobject, new_label))
        return AnimationGroup(*animations)


class ThreadMobject(VGroup):
    """Represents a Coroutine Thread."""
    def __init__(self, thread_id: str, initial_state="Available", width=2.3, height=2.5, **kwargs):
        super().__init__(**kwargs)
        self.thread_id = thread_id
        self.box = Rectangle(width=width, height=height, color=BLUE_COLOR, stroke_width=2)
        self.label = Text(f"Thread {thread_id}", font_size=18).next_to(self.box, UP, buff=0.1)

        # State Label
        self.state_label = Text(f"State: {initial_state}", font_size=16, color=YELLOW).next_to(self.label, UP, buff=0.1)

        # Stack Area (simplified visual)
        self.stack_box = Rectangle(width=width * 0.4, height=height * 0.6, color=GREY_BROWN, fill_opacity=0.3)
        self.stack_label = Text("Stack", font_size=14).next_to(self.stack_box, DOWN, buff=0.1)
        self.stack_group = VGroup(self.stack_box, self.stack_label).align_to(self.box, LEFT).shift(RIGHT * 0.1 + DOWN * 0.1)

        # Context Area (simplified visual)
        self.ctx_box = Rectangle(width=width * 0.4, height=height * 0.6, color=GREY_BROWN, fill_opacity=0.3)
        self.ctx_label = Text("Ctx", font_size=14).next_to(self.ctx_box, DOWN, buff=0.1)
        self.ctx_registers = VGroup( # Placeholder for saved registers
             Text("rsp: -", font_size=24),
             Text("rip: -", font_size=24),
             Text("...", font_size=24)
        ).arrange(DOWN, buff=0.05).move_to(self.ctx_box.get_center())
        self.ctx_group = VGroup(self.ctx_box, self.ctx_label, self.ctx_registers).align_to(self.box, RIGHT).shift(LEFT * 0.1 + DOWN * 0.1)


        self.add(self.box, self.label, self.state_label, self.stack_group, self.ctx_group)

    def update_state(self, new_state: str):
        """Returns an animation to update the state label."""
        # new_label = Text(f"State: {new_state}", font_size=self.state_label.font_size, color=YELLOW)
        new_label = Text(f"State: {new_state}", font_size=16, color=YELLOW)
        new_label.move_to(self.state_label)
        return Transform(self.state_label, new_label)

    def update_ctx(self, ctx_values: dict):
        """Returns an animation to update the context register values."""
        animations = []
        # Simplified: just update rsp and rip for now
        rsp_label = self.ctx_registers[0]
        rip_label = self.ctx_registers[1]

        new_rsp_text = f"rsp: {ctx_values.get('rsp', '-')}"
        new_rip_text = f"rip: {ctx_values.get('rip', '-')}"

        # new_rsp_label = Text(new_rsp_text, font_size=rsp_label.font_size).move_to(rsp_label).align_to(rsp_label, LEFT)
        # new_rip_label = Text(new_rip_text, font_size=rip_label.font_size).move_to(rip_label).align_to(rip_label, LEFT)
        new_rsp_label = Text(new_rsp_text, font_size=24).move_to(rsp_label).align_to(rsp_label, LEFT)
        new_rip_label = Text(new_rip_text, font_size=24).move_to(rip_label).align_to(rip_label, LEFT)

        animations.append(Transform(rsp_label, new_rsp_label))
        animations.append(Transform(rip_label, new_rip_label))
        return AnimationGroup(*animations)

    def get_stack_top_pos(self):
        """Returns the position near the top of the stack box."""
        return self.stack_box.get_top() + DOWN * 0.2

    def get_stack_bottom_pos(self):
        """Returns the position near the bottom of the stack box."""
        return self.stack_box.get_bottom() + UP * 0.2


class RuntimeBox(VGroup):
    """Represents the Runtime."""
    def __init__(self, width=3, height=4, **kwargs):
        super().__init__(**kwargs)
        self.box = Rectangle(width=width, height=height, color=BLUE_COLOR, stroke_width=2)
        self.label = Text("Runtime", font_size=20).next_to(self.box, UP, buff=0.1)

        # Placeholder for threads list visual
        self.threads_area = Rectangle(width=width * 0.8, height=height * 0.6, color=DARK_GREY, fill_opacity=0.2)
        self.threads_label = Text("threads:", font_size=16).next_to(self.threads_area, UP, buff=0.1, aligned_edge=LEFT)
        self.threads_group = VGroup(self.threads_area, self.threads_label).move_to(self.box.get_center()).shift(DOWN*0.3)

        # Placeholder for current pointer
        self.current_label = Text("current: T?", font_size=20).next_to(self.threads_group, DOWN, buff=0.1)

        self.add(self.box, self.label, self.threads_group, self.current_label)

    def update_current(self, thread_id: str):
        """Returns an animation to update the current thread label."""
        new_label = Text(f"current: T{thread_id}", font_size=self.current_label.font_size)
        new_label.move_to(self.current_label)
        return Transform(self.current_label, new_label)
