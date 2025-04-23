from manim import *
import sys
import os

# Add bili_lib to path to import components
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from bili_lib.visuals.components import OSThreadBox, CPUBox, ThreadMobject, RuntimeBox, BLUE_COLOR

# --- Constants ---
STACK_ITEM_COLOR = GREEN_C
CODE_COLOR = ORANGE
POINTER_COLOR = RED

# --- Scene Definition ---
class CoroutineLifecycle(Scene):
    def construct(self):
        # --- Phase 0: Setup Scene ---
        self.camera.background_color = BLACK
        os_thread, runtime_box, cpu_box, threads = self._setup_scene_elements()
        self.wait(1)

        # Store references for easy access and potential cleanup
        self.os_thread = os_thread
        self.runtime_box = runtime_box
        self.cpu_box = cpu_box
        self.threads = threads

        # --- Phase 1: Initialization & Spawn T1 ---
        phase1_title = self._show_phase_title("Phase 1: Init & Spawn T1")

        # 1.1 Show Runtime::new() and init()
        runtime_init_code = Code(
            code_string="let mut runtime = Runtime::new();\nruntime.init();",
            language="rust",
            formatter_style="default", # Use formatter_style
            paragraph_config={"font_size": 18} # Pass font_size via paragraph_config
        ).next_to(runtime_box, DOWN, buff=0.3).align_to(runtime_box, LEFT)

        self.play(FadeIn(runtime_init_code))
        # Animate runtime.current pointing to T0
        self.play(runtime_box.update_current("0"))
        self.wait(1)
        self.play(FadeOut(runtime_init_code))

        # 1.2 Spawn T1 using helper method
        thread1 = self.threads["T1"]
        t1_initial_rsp_val = f"0x...{thread1.thread_id}F1"
        t1_spawn_mobjects = self._spawn_thread(thread1, "T1 Func", t1_initial_rsp_val)

        # Cleanup Phase 1 visuals
        self._cleanup_mobjects(*t1_spawn_mobjects, phase1_title)
        self.wait(0.5)


        # --- Phase 2: Spawn T2 ---
        phase2_title = self._show_phase_title("Phase 2: Spawn T2")

        # 2.1 Spawn T2 using helper method
        thread2 = self.threads["T2"]
        t2_initial_rsp_val = f"0x...{thread2.thread_id}F2"
        t2_spawn_mobjects = self._spawn_thread(thread2, "T2 Func", t2_initial_rsp_val)

        # Cleanup Phase 2 visuals
        self._cleanup_mobjects(*t2_spawn_mobjects, phase2_title)
        self.wait(0.5)


        # --- Phase 3: Run & First Yield (T0 -> T1) ---
        phase3_title = self._show_phase_title("Phase 3: Yield T0 -> T1")

        # 3.1 Show runtime.run() leading to t_yield()
        run_code = Code(
            code_string="runtime.run() {\n  // loop {\n    t_yield();\n  // }\n}",
            language="rust", formatter_style="default", paragraph_config={"font_size": 18}
        ).next_to(os_thread, DOWN, buff=0.3).align_to(os_thread, LEFT)
        yield_code = Code(
            code_string="t_yield() {\n  // 1. Find next ready thread\n  // 2. Switch context\n}",
            language="rust", formatter_style="default", paragraph_config={"font_size": 18}
        ).next_to(run_code, RIGHT, buff=0.5)

        self.play(FadeIn(run_code))
        self.wait(0.5)
        self.play(FadeIn(yield_code))
        self.wait(1)

        # 3.2 Define contexts and code snippet for the switch
        thread0 = self.threads["T0"]
        thread1 = self.threads["T1"]
        t0_runtime_regs = {"rsp": "0x...T0SP", "rip": "0x...T0IP", "rbx": "0xT0BX", "rbp": "0xT0BP", "r12": "0xT012"} # Context T0 saves when yielding
        t1_initial_ctx = {"rsp": t1_initial_rsp_val, "rip": f"0x...F1", "rbx": "0x0", "rbp": "0x0", "r12": "0x0"} # Context T1 loads initially
        t1_code = Code(
            code_string="fn thread1_func() {\n  println!(\"T1 running\");\n  // ... yield ...\n}",
            language="rust", formatter_style="default", paragraph_config={"font_size": 16}
        ).next_to(thread1, DOWN, buff=0.3)

        # 3.3 Show switch call
        switch_code = Code(
            code_string="// Get old_ctx (T0), new_ctx (T1)\nswitch(old_ctx, new_ctx);",
            language="rust", formatter_style="default", paragraph_config={"font_size": 18}
        ).next_to(yield_code, RIGHT, buff=0.5)
        self.play(FadeIn(switch_code))
        self.wait(1)

        # 3.4 Perform context switch using helper
        switch_mobjects_p3 = self._context_switch(
            from_thread=thread0,
            to_thread=thread1,
            from_regs_to_save=t0_runtime_regs,
            to_regs_to_load=t1_initial_ctx,
            to_code_mobject=t1_code,
            switch_title_text="Context Switch: T0 -> T1",
            from_state="Ready", # T0 becomes Ready
            to_state="Running"  # T1 becomes Running
        )

        # Cleanup Phase 3 visuals (Keep t1_code and self.control_flow_arrow)
        self._cleanup_mobjects(run_code, yield_code, switch_code, phase3_title, *switch_mobjects_p3)
        self.wait(0.5)


        # --- Phase 4: T1 Executes & Yields (T1 -> T2) ---
        phase4_title = self._show_phase_title("Phase 4: Yield T1 -> T2")

        # 4.1 T1 code execution simulation
        thread1 = self.threads["T1"]
        thread2 = self.threads["T2"]
        cpu_box = self.cpu_box
        runtime_box = self.runtime_box

        t1_running_regs = t1_initial_ctx.copy() # t1_initial_ctx from Phase 3
        t1_running_regs["rsp"] = "0x...T1SP_mid"
        t1_running_regs["rip"] = "0x...T1_yield"
        self.play(cpu_box.update_registers(t1_running_regs), run_time=0.5)
        # Highlight yield in T1's code (t1_code from Phase 3)
        yield_line_highlight = SurroundingRectangle(t1_code[-1], color=YELLOW, buff=0.05)
        self.play(Create(yield_line_highlight))
        self.wait(1)

        # 4.2 Show yield and switch logic
        self.play(FadeIn(yield_code)) # yield_code from Phase 3
        self.wait(1)
        self.play(FadeIn(switch_code)) # switch_code from Phase 3
        self.wait(1)

        # 4.3 Define T2's initial context and code snippet
        t2_initial_ctx = {"rsp": t2_initial_rsp_val, "rip": f"0x...F2", "rbx": "0x0", "rbp": "0x0", "r12": "0x0"} # t2_initial_rsp_val from Phase 2
        t2_code = Code(
            code_string="fn thread2_func() {\n  println!(\"T2 running\");\n  // ... yield ...\n}",
            language="rust", formatter_style="default", paragraph_config={"font_size": 16}
        ).next_to(thread2, DOWN, buff=0.3)

        # 4.4 Fade out T1 code before switching
        self.play(FadeOut(t1_code), FadeOut(yield_line_highlight))

        # 4.5 Perform context switch T1 -> T2
        switch_mobjects_p4 = self._context_switch(
            from_thread=thread1,
            to_thread=thread2,
            from_regs_to_save=t1_running_regs, # T1's state when yielding
            to_regs_to_load=t2_initial_ctx,    # T2's initial state
            to_code_mobject=t2_code,
            switch_title_text="Context Switch: T1 -> T2",
            from_state="Ready",
            to_state="Running"
        )

        # Cleanup Phase 4 visuals (Keep t2_code and self.control_flow_arrow)
        self._cleanup_mobjects(yield_code, switch_code, phase4_title, *switch_mobjects_p4)
        self.wait(0.5)


        # --- Phase 5: T2 Executes & Yields (T2 -> T1) ---
        phase5_title = self._show_phase_title("Phase 5: Yield T2 -> T1")

        # 5.1 T2 code execution simulation
        thread1 = self.threads["T1"] # Re-get reference if needed
        thread2 = self.threads["T2"] # Re-get reference if needed
        cpu_box = self.cpu_box       # Re-get reference if needed
        runtime_box = self.runtime_box # Re-get reference if needed

        t2_running_regs = t2_initial_ctx.copy() # t2_initial_ctx from Phase 4
        t2_running_regs["rsp"] = "0x...T2SP_mid"
        t2_running_regs["rip"] = "0x...T2_yield"
        self.play(cpu_box.update_registers(t2_running_regs), run_time=0.5)
        # Highlight yield in T2's code (t2_code from Phase 4)
        yield_line_highlight_t2 = SurroundingRectangle(t2_code[-1], color=YELLOW, buff=0.05)
        self.play(Create(yield_line_highlight_t2))
        self.wait(1)

        # 5.2 Show yield and switch logic
        self.play(FadeIn(yield_code)) # yield_code from Phase 3/4
        self.wait(1)
        self.play(FadeIn(switch_code)) # switch_code from Phase 3/4
        self.wait(1)

        # 5.3 Define T1's code snippet for resuming
        # t1_saved_ctx is the state T1 was saved in during Phase 4 (t1_running_regs)
        t1_saved_ctx = t1_running_regs
        t1_code_resume = Code(
            code_string="fn thread1_func() {\n  println!(\"T1 running\");\n  // ... yield ...\n}",
            language="rust", formatter_style="default", paragraph_config={"font_size": 16}
        ).next_to(thread1, DOWN, buff=0.3)

        # 5.4 Fade out T2 code before switching
        self.play(FadeOut(t2_code), FadeOut(yield_line_highlight_t2))

        # 5.5 Perform context switch T2 -> T1
        switch_mobjects_p5 = self._context_switch(
            from_thread=thread2,
            to_thread=thread1,
            from_regs_to_save=t2_running_regs, # T2's state when yielding
            to_regs_to_load=t1_saved_ctx,      # T1's previously saved state
            to_code_mobject=t1_code_resume,
            switch_title_text="Context Switch: T2 -> T1",
            from_state="Ready",
            to_state="Running"
        )

        # 5.6 Highlight instruction after yield in T1's resumed code
        resume_highlight = SurroundingRectangle(t1_code_resume[2], color=GREEN_C, buff=0.05) # Assuming yield is line 3 (index 2)
        self.play(Create(resume_highlight))
        self.wait(1)

        # Cleanup Phase 5 visuals (Keep t1_code_resume and self.control_flow_arrow)
        self._cleanup_mobjects(yield_code, switch_code, phase5_title, resume_highlight, *switch_mobjects_p5)
        self.wait(0.5)


        # --- Phase 6: T1 Finishes & Enters Guard ---
        phase6_title = self._show_phase_title("Phase 6: T1 Finishes -> Guard")

        # 6.1 Define necessary mobjects and contexts
        thread0 = self.threads["T0"] # Re-get reference
        thread1 = self.threads["T1"] # Re-get reference
        thread2 = self.threads["T2"] # Re-get reference
        cpu_box = self.cpu_box       # Re-get reference

        # Context T1 was in when it resumed in Phase 5
        t1_cpu_state_before_ret = t1_saved_ctx

        # Code mobjects needed for the helper
        guard_code = Code(
            code_string="fn guard() {\n  // Set state = Available\n  t_yield();\n}",
            language="rust", formatter_style="default", paragraph_config={"font_size": 16}
        ) # Positioned by helper
        # Recreate yield_code and switch_code if they were cleaned up
        yield_code = Code(
            code_string="t_yield() {\n  // 1. Find next ready thread\n  // 2. Switch context\n}",
            language="rust", formatter_style="default", paragraph_config={"font_size": 18}
        ).next_to(self.runtime_box, DOWN, buff=0.3).shift(RIGHT*1.5) # Adjust position
        switch_code = Code(
            code_string="// Get old_ctx, new_ctx\nswitch(old_ctx, new_ctx);",
            language="rust", formatter_style="default", paragraph_config={"font_size": 18}
        ).next_to(yield_code, RIGHT, buff=0.5)

        # Saved contexts from previous phases needed for the final switch
        # t0_runtime_regs from Phase 3
        # t1_saved_ctx = t1_running_regs from Phase 4 (already have as t1_saved_ctx)
        # t2_running_regs from Phase 5

        # 6.2 Call the thread finishing helper
        finish_mobjects_p6 = self._thread_finishes(
            finished_thread=thread1,
            next_thread_to_run=thread2,
            current_cpu_regs=t1_cpu_state_before_ret,
            finished_thread_code_mobject=t1_code_resume, # From Phase 5
            guard_code_mobject=guard_code,
            yield_code_mobject=yield_code,
            switch_code_mobject=switch_code,
            t0_saved_ctx=t0_runtime_regs, # From Phase 3
            t1_saved_ctx=t1_saved_ctx,    # From Phase 4/5
            t2_saved_ctx=t2_running_regs  # From Phase 5
        )

        # 6.3 Extract the resuming code mobject (T2's code) if needed later
        # The helper returns a list, the last element might be the resuming code
        t2_code_resume = finish_mobjects_p6[-1] if finish_mobjects_p6 and isinstance(finish_mobjects_p6[-1], Code) else None

        # Cleanup Phase 6 visuals (Keep t2_code_resume and self.control_flow_arrow)
        # We need to exclude t2_code_resume from cleanup if it exists
        mobjects_to_clean_p6 = [m for m in finish_mobjects_p6 if m != t2_code_resume]
        self._cleanup_mobjects(phase6_title, yield_code, switch_code, *mobjects_to_clean_p6) # Clean yield/switch explicitly if shown by helper
        self.wait(0.5)


        # --- Phase 7: T2 Finishes & Runtime Ends ---
        phase7_title = self._show_phase_title("Phase 7: T2 Finishes & Runtime Ends")

        # 7.1 Define necessary mobjects and contexts
        thread0 = self.threads["T0"] # Re-get reference
        thread1 = self.threads["T1"] # Re-get reference (needed for t1_saved_ctx)
        thread2 = self.threads["T2"] # Re-get reference
        cpu_box = self.cpu_box       # Re-get reference

        # Context T2 was in when it resumed in Phase 6
        # This is t2_saved_ctx from Phase 5 (t2_running_regs)
        t2_cpu_state_before_ret = t2_running_regs

        # Code mobjects needed for the helper
        guard_code = Code(
            code_string="fn guard() {\n  // Set state = Available\n  t_yield();\n}",
            language="rust", formatter_style="default", paragraph_config={"font_size": 16}
        ) # Positioned by helper
        # Recreate yield_code and switch_code if they were cleaned up or create them fresh
        yield_code = Code(
            code_string="t_yield() {\n  // 1. Find next ready thread\n  // 2. Switch context\n}",
            language="rust", formatter_style="default", paragraph_config={"font_size": 18}
        ).next_to(self.runtime_box, DOWN, buff=0.3).shift(RIGHT*1.5) # Adjust position as needed
        switch_code = Code(
            code_string="// Get old_ctx, new_ctx\nswitch(old_ctx, new_ctx);",
            language="rust", formatter_style="default", paragraph_config={"font_size": 18}
        ).next_to(yield_code, RIGHT, buff=0.5) # Adjust position as needed

        # Saved contexts from previous phases needed for the final switch
        # t0_runtime_regs from Phase 3
        # t1_saved_ctx from Phase 5
        # t2_running_regs from Phase 5 (now t2_cpu_state_before_ret)

        # 7.2 Call the thread finishing helper
        finish_mobjects_p7 = self._thread_finishes(
            finished_thread=thread2,
            next_thread_to_run=None, # Signal to switch back to T0
            current_cpu_regs=t2_cpu_state_before_ret,
            finished_thread_code_mobject=t2_code_resume, # From Phase 6 cleanup
            guard_code_mobject=guard_code,
            yield_code_mobject=yield_code,
            switch_code_mobject=switch_code,
            t0_saved_ctx=t0_runtime_regs, # From Phase 3
            t1_saved_ctx=t1_saved_ctx,    # From Phase 5
            t2_saved_ctx=t2_cpu_state_before_ret # From Phase 5
        )

        # 7.3 Show runtime loop ending
        # run_code was cleaned up in Phase 3, recreate if needed or use a placeholder position
        runtime_ends_text = Text("runtime.run() loop finishes", font_size=18, color=RED).next_to(self.runtime_box, DOWN, buff=0.3).align_to(self.runtime_box, LEFT)
        self.play(FadeIn(runtime_ends_text))
        self.wait(1)

        # Cleanup Phase 7 visuals
        # The _thread_finishes helper returns mobjects it created/managed
        # We also need to clean up yield_code, switch_code, runtime_ends_text, phase7_title, and the control flow arrow
        self._cleanup_mobjects(
            phase7_title,
            yield_code, # Explicitly clean up yield_code shown in helper
            switch_code, # Explicitly clean up switch_code shown in helper
            runtime_ends_text,
            self.control_flow_arrow,
            *finish_mobjects_p7 # Unpack the list returned by the helper
        )
        # Remove the arrow reference as it's faded out
        if hasattr(self, 'control_flow_arrow'):
            del self.control_flow_arrow
        self.wait(0.5)


        # Final message
        final_text = Text("Animation Complete!", font_size=36, color=BLUE_COLOR)
        self.play(Write(final_text))
        self.wait(3)


    # --- Helper Methods for Refactoring ---

    def _setup_scene_elements(self):
        """Creates and positions the main visual components."""
        box_buff = 0.2
        box_scale = 0.6

        os_thread = OSThreadBox().scale(box_scale).to_edge(UL, buff=0.4)
        runtime_box = RuntimeBox().scale(box_scale).next_to(os_thread.box, RIGHT, buff=box_buff).align_to(os_thread.box, UP)
        cpu_box = CPUBox().scale(box_scale).next_to(runtime_box.box, RIGHT, buff=box_buff).align_to(os_thread.box, UP)

        thread_scale = 1
        thread_buff = 0.6
        thread0 = ThreadMobject("0", initial_state="Running").scale(thread_scale)
        thread0.move_to(os_thread.box.get_corner(DL) + UP * (thread0.get_height() / 2 ) + RIGHT * (thread0.get_width() / 2 + 0.3))
        thread1 = ThreadMobject("1", initial_state="Available").scale(thread_scale).next_to(thread0, RIGHT, buff=thread_buff)
        thread2 = ThreadMobject("2", initial_state="Available").scale(thread_scale).next_to(thread1, RIGHT, buff=thread_buff)
        threads = {"T0": thread0, "T1": thread1, "T2": thread2}

        self.play(
            Create(os_thread),
            Create(runtime_box),
            Create(cpu_box),
            Create(thread0),
            Create(thread1),
            Create(thread2)
        )
        return os_thread, runtime_box, cpu_box, threads

    def _show_phase_title(self, title_text):
        """Displays a phase title at the bottom edge."""
        title = Text(title_text, font_size=24, color=WHITE).to_edge(DOWN)
        self.play(Write(title))
        return title # Return the mobject for later cleanup

    def _cleanup_mobjects(self, *mobjects):
        """Fades out a list of mobjects."""
        # Filter out None values in case some mobjects weren't created
        valid_mobjects = [m for m in mobjects if m is not None]
        if valid_mobjects:
            self.play(*[FadeOut(m) for m in valid_mobjects])

    def _spawn_thread(self, thread_to_spawn, thread_func_name, initial_rsp_val):
        """Handles the animation sequence for spawning a new thread."""
        spawn_code = Code(
            code_string=f"runtime.spawn(|| {{\n  // {thread_func_name} function body...\n}});",
            language="rust",
            formatter_style="default",
            paragraph_config={"font_size": 18}
        ).next_to(self.os_thread, DOWN, buff=0.3).align_to(self.os_thread, LEFT)
        self.play(FadeIn(spawn_code))
        self.play(Indicate(thread_to_spawn.box, color=YELLOW, scale_factor=1.1))

        stack_setup_title = Text(f"Setting up {thread_to_spawn.label.text} Stack", font_size=18, color=WHITE).next_to(thread_to_spawn.stack_box, UP, buff=0.2)
        self.play(Write(stack_setup_title))

        stack_top = thread_to_spawn.get_stack_top_pos()
        guard_addr = Text("G (Guard)", font_size=12, color=STACK_ITEM_COLOR).move_to(stack_top + DOWN * 0.2)
        skip_addr = Text("S (Skip)", font_size=12, color=STACK_ITEM_COLOR).next_to(guard_addr, DOWN, buff=0.1)
        func_addr = Text(f"F{thread_to_spawn.thread_id} ({thread_func_name})", font_size=12, color=STACK_ITEM_COLOR).next_to(skip_addr, DOWN, buff=0.1)

        rsp_pointer = Arrow(
            start=thread_to_spawn.ctx_registers[0].get_right() + RIGHT*0.1,
            end=func_addr.get_left() + LEFT*0.1,
            buff=0.1, stroke_width=2, max_tip_length_to_length_ratio=0.1, color=POINTER_COLOR
        )
        rsp_pointer_label = Text("ctx.rsp", font_size=12, color=POINTER_COLOR).next_to(rsp_pointer, UP, buff=0.05)

        self.play(
            FadeIn(guard_addr, shift=DOWN*0.2),
            FadeIn(skip_addr, shift=DOWN*0.2),
            FadeIn(func_addr, shift=DOWN*0.2),
            run_time=1.5
        )
        self.play(
            thread_to_spawn.update_ctx({"rsp": initial_rsp_val}),
            Create(rsp_pointer),
            Write(rsp_pointer_label)
        )
        self.wait(1)
        self.play(thread_to_spawn.update_state("Ready"))
        self.wait(1)

        # Return temporary mobjects for cleanup
        return spawn_code, stack_setup_title, guard_addr, skip_addr, func_addr, rsp_pointer, rsp_pointer_label

    def _context_switch(self, from_thread, to_thread, from_regs_to_save, to_regs_to_load, to_code_mobject, switch_title_text, from_state="Ready", to_state="Running"):
        """Handles the animation sequence for a context switch."""
        # Scheduling indication
        self.play(Indicate(from_thread.box, color=GREEN))
        self.wait(0.5)
        self.play(Indicate(to_thread.box, color=YELLOW))
        self.wait(1)

        # State Transitions & Runtime Update
        self.play(
            from_thread.update_state(from_state),
            to_thread.update_state(to_state),
            self.runtime_box.update_current(to_thread.thread_id)
        )
        self.wait(1)

        # Show switch call (assuming yield_code and switch_code are managed outside)
        # switch_code = Code(...) # Defined and shown outside this helper
        # self.play(FadeIn(switch_code))
        # self.wait(1)

        # Context Switch Animation
        switch_title = Text(switch_title_text, font_size=18, color=WHITE).next_to(self.cpu_box, DOWN, buff=0.3)
        # Check if a switch title already exists to transform it
        existing_switch_title = next((m for m in self.mobjects if isinstance(m, Text) and "Context Switch:" in m.text), None)
        if existing_switch_title:
            self.play(Transform(existing_switch_title, switch_title))
            switch_title_to_clean = existing_switch_title # Clean the transformed one
        else:
            self.play(Write(switch_title))
            switch_title_to_clean = switch_title # Clean the new one

        # Save 'from' context
        self.play(self.cpu_box.update_registers(from_regs_to_save)) # Assume CPU holds these values
        self.wait(0.5)
        save_arrows = VGroup()
        for i, reg_label in enumerate(self.cpu_box.registers):
            # Check if the register exists in the thread's context display
            if i < len(from_thread.ctx_registers) and from_thread.ctx_registers[i].text != "...":
                 arrow = Arrow(start=reg_label.get_right(), end=from_thread.ctx_registers[i].get_left(), buff=0.1, stroke_width=1, max_tip_length_to_length_ratio=0.1, color=ORANGE)
                 save_arrows.add(arrow)
        save_text = Text(f"Save T{from_thread.thread_id} Ctx", font_size=14, color=ORANGE).next_to(save_arrows, LEFT, buff=0.1)
        self.play(Create(save_arrows), Write(save_text))
        self.play(from_thread.update_ctx(from_regs_to_save))
        self.wait(1)
        self.play(FadeOut(save_arrows), FadeOut(save_text))

        # Load 'to' context
        load_arrows = VGroup()
        for i, reg_label in enumerate(self.cpu_box.registers):
             if i < len(to_thread.ctx_registers) and to_thread.ctx_registers[i].text != "...":
                 arrow = Arrow(start=to_thread.ctx_registers[i].get_right(), end=reg_label.get_left(), buff=0.1, stroke_width=1, max_tip_length_to_length_ratio=0.1, color=GREEN)
                 load_arrows.add(arrow)
        load_text = Text(f"Load T{to_thread.thread_id} Ctx", font_size=14, color=GREEN).next_to(load_arrows, RIGHT, buff=0.1)
        self.play(Create(load_arrows), Write(load_text))
        self.play(self.cpu_box.update_registers(to_regs_to_load))
        self.wait(1)
        self.play(FadeOut(load_arrows), FadeOut(load_text))

        # Jump to 'to' code
        rip_indicator = SurroundingRectangle(self.cpu_box.registers[1], buff=0.05, color=RED) # Highlight RIP
        new_control_flow_arrow = Arrow(
            start=self.cpu_box.box.get_bottom(),
            end=to_code_mobject.get_top(),
            color=RED, stroke_width=3
        )

        # Check if control_flow_arrow exists and transform, otherwise create
        if hasattr(self, 'control_flow_arrow') and self.control_flow_arrow in self.mobjects:
             self.play(
                 Create(rip_indicator),
                 FadeIn(to_code_mobject, shift=UP),
                 Transform(self.control_flow_arrow, new_control_flow_arrow)
             )
        else:
             self.play(Create(rip_indicator))
             self.wait(0.5)
             self.play(FadeIn(to_code_mobject, shift=UP), Create(new_control_flow_arrow))
             self.control_flow_arrow = new_control_flow_arrow # Store the new arrow

        self.wait(1)

        # Return temporary mobjects for cleanup
        return switch_title_to_clean, rip_indicator # Arrows/text faded out, arrow managed via self.control_flow_arrow

    def _thread_finishes(self, finished_thread, next_thread_to_run, current_cpu_regs, finished_thread_code_mobject, guard_code_mobject, yield_code_mobject, switch_code_mobject, t0_saved_ctx, t1_saved_ctx, t2_saved_ctx):
        """Handles the animation sequence when a thread function returns and enters the guard."""
        # Conceptual 'ret'
        ret_text = Text(f"T{finished_thread.thread_id} func returns (ret)", font_size=16, color=CODE_COLOR).move_to(finished_thread_code_mobject)
        # Ensure the finished code mobject exists before trying to fade it out
        if finished_thread_code_mobject in self.mobjects:
            self.play(FadeOut(finished_thread_code_mobject), FadeIn(ret_text))
        else:
            # If the code mobject was already removed (e.g., by a previous cleanup), just fade in ret_text
            ret_text.move_to(self.control_flow_arrow.get_end()) # Position it where the code was expected
            self.play(FadeIn(ret_text))
        self.wait(1)

        # Pop Guard address
        guard_addr_vis = Text("G (Guard)", font_size=12, color=STACK_ITEM_COLOR).move_to(finished_thread.get_stack_top_pos() + DOWN * 0.2)
        # Recreate stack visuals if they were cleaned up previously
        # For simplicity, assume they might be gone and recreate
        # skip_addr_vis = Text("S (Skip)", ...).next_to(guard_addr_vis, ...)
        # func_addr_vis = Text(f"F{finished_thread.thread_id}...", ...).next_to(skip_addr_vis, ...)
        # self.add(guard_addr_vis, skip_addr_vis, func_addr_vis) # Add without animation
        self.add(guard_addr_vis) # Simplified: just show guard

        pop_arrow = Arrow(start=guard_addr_vis.get_top(), end=self.cpu_box.registers[1].get_bottom(), buff=0.1, stroke_width=2, color=PURPLE)
        pop_text = Text("ret pops G", font_size=14, color=PURPLE).next_to(pop_arrow, LEFT)

        guard_rip_regs = current_cpu_regs.copy()
        guard_rip_regs["rip"] = "0x...Guard"

        self.play(Indicate(guard_addr_vis), Create(pop_arrow), Write(pop_text))
        self.wait(0.5)
        self.play(self.cpu_box.update_registers(guard_rip_regs))
        self.play(FadeOut(pop_arrow), FadeOut(pop_text), FadeOut(ret_text), FadeOut(guard_addr_vis)) # Also fade out other stack items if recreated
        self.wait(1)

        # Execute Guard
        # Move guard code visual near the finished thread
        guard_code_mobject.next_to(finished_thread, DOWN, buff=0.3)
        self.play(
            Transform(self.control_flow_arrow, Arrow(start=self.cpu_box.box.get_bottom(), end=guard_code_mobject.get_top(), color=RED, stroke_width=3)),
            FadeIn(guard_code_mobject)
        )
        self.wait(1)

        # Guard sets state and yields
        self.play(finished_thread.update_state("Available"))
        self.wait(1)
        guard_yield_highlight = SurroundingRectangle(guard_code_mobject[-1], color=YELLOW, buff=0.05)
        self.play(Create(guard_yield_highlight))
        self.play(FadeIn(yield_code_mobject)) # Show yield logic inside helper
        self.wait(1)

        # Scheduling (inside guard's yield)
        self.play(Indicate(finished_thread.box, color=GREEN)) # Still 'current' technically
        self.wait(0.5)

        no_ready_text = None # Initialize potential temporary mobject
        if next_thread_to_run:
            self.play(Indicate(next_thread_to_run.box, color=YELLOW))
            self.wait(1)
            next_state = "Running"
            next_runtime_id = next_thread_to_run.thread_id
            # Determine context to load based on the next thread
            if next_thread_to_run.thread_id == "1":
                next_thread_saved_ctx = t1_saved_ctx
            elif next_thread_to_run.thread_id == "2":
                next_thread_saved_ctx = t2_saved_ctx
            else: # Should not happen in this specific scenario, but handle defensively
                next_thread_saved_ctx = {}
        else:
            # Special case: No other ready thread, switch back to T0 (runtime)
            no_ready_text = Text("No other Ready threads found", font_size=16, color=RED).next_to(yield_code_mobject, DOWN)
            self.play(Write(no_ready_text))
            self.wait(1)
            self.play(Indicate(self.threads["T0"].box, color=YELLOW)) # Indicate T0
            self.wait(1)
            next_thread_to_run = self.threads["T0"]
            next_state = "Running" # T0 becomes running
            next_runtime_id = "0"
            next_thread_saved_ctx = t0_saved_ctx # Use T0's saved context


        # Prepare for Context Switch (Guard -> Next Thread)
        self.play(FadeIn(switch_code_mobject)) # Show switch logic inside helper
        self.wait(1)

        guard_yield_regs = guard_rip_regs.copy()
        guard_yield_regs["rip"] = "0x...GuardYield" # RIP after yield in guard

        # Determine the code mobject for the resuming thread (or None if T0)
        resuming_code_mobject = None
        if next_thread_to_run.thread_id == "1":
             # Need a way to get/recreate T1's code mobject
             resuming_code_mobject = Code(code_string="fn thread1_func() {\n  println!(\"T1 running\");\n  // ... yield ...\n}", language="rust", formatter_style="default", paragraph_config={"font_size": 16}).next_to(self.threads["T1"], DOWN, buff=0.3)
        elif next_thread_to_run.thread_id == "2":
             # Need a way to get/recreate T2's code mobject
             resuming_code_mobject = Code(code_string="fn thread2_func() {\n  println!(\"T2 running\");\n  // ... yield ...\n}", language="rust", formatter_style="default", paragraph_config={"font_size": 16}).next_to(self.threads["T2"], DOWN, buff=0.3)


        switch_title_text = f"Context Switch: T{finished_thread.thread_id}(Guard) -> T{next_thread_to_run.thread_id}"

        # Perform the switch animation
        switch_mobjects = self._context_switch(
            from_thread=finished_thread,
            to_thread=next_thread_to_run,
            from_regs_to_save=guard_yield_regs,
            to_regs_to_load=next_thread_saved_ctx,
            to_code_mobject=resuming_code_mobject if resuming_code_mobject else self.runtime_box, # Point arrow to runtime if T0
            switch_title_text=switch_title_text,
            from_state="Available", # Guard leaves finished thread as Available
            to_state=next_state
        )

        # Additional animations after switch if resuming a thread
        resume_highlight = None
        if resuming_code_mobject:
             # Highlight instruction after yield (conceptual)
             # Find the line index corresponding to the instruction after yield
             resume_line_index = 2 # Assuming yield is the 3rd line (index 2) in the snippet
             if len(resuming_code_mobject) > resume_line_index:
                 resume_highlight = SurroundingRectangle(resuming_code_mobject[resume_line_index], color=GREEN_C, buff=0.05)
                 self.play(Create(resume_highlight))
                 self.wait(1)
        else:
             # Pointing back to runtime (T0)
             self.play(Transform(self.control_flow_arrow, Arrow(start=self.cpu_box.box.get_bottom(), end=self.runtime_box.box.get_left(), color=RED, stroke_width=3)))
             # Optionally show runtime loop ending text
             # runtime_ends_text = Text("runtime.run() loop finishes", font_size=18, color=RED).next_to(self.runtime_box, DOWN)
             # self.play(FadeIn(runtime_ends_text))


        # Return temporary mobjects for cleanup
        cleanup_items = [
            guard_code_mobject, guard_yield_highlight,
            no_ready_text, # Will be None if not created
            resume_highlight, # Will be None if not created
            resuming_code_mobject, # Will be None if T0
            # runtime_ends_text # If created
        ] + list(switch_mobjects) # Add mobjects returned by _context_switch

        # Also return the resuming code mobject if it was created, so it can be used/cleaned up later
        cleanup_items.append(resuming_code_mobject)

        return cleanup_items
