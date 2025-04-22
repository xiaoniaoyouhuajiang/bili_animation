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
        self.camera.background_color = WHITE # Use white background for better contrast maybe? Or keep default? Let's try white.
        # Manim's default color is BLACK, let's revert if white is not good.
        # self.camera.background_color = BLACK

        # Create main containers
        os_thread = OSThreadBox().scale(0.9).to_edge(UL, buff=0.5)
        runtime_box = RuntimeBox().next_to(os_thread.box, RIGHT, buff=0.5).align_to(os_thread.box, UP)
        cpu_box = CPUBox().next_to(runtime_box.box, RIGHT, buff=0.5).align_to(os_thread.box, UP)

        # Create Thread Mobjects (T0, T1, T2)
        # T0 (base thread) - starts as Running (simplified)
        thread0 = ThreadMobject("0", initial_state="Running").next_to(os_thread.box, DOWN, buff=0.5).align_to(os_thread.box, LEFT).shift(RIGHT*0.5)
        # T1 and T2 - start as Available
        thread1 = ThreadMobject("1", initial_state="Available").next_to(thread0, RIGHT, buff=0.5)
        thread2 = ThreadMobject("2", initial_state="Available").next_to(thread1, RIGHT, buff=0.5)

        threads = {"T0": thread0, "T1": thread1, "T2": thread2}

        self.play(
            Create(os_thread),
            Create(runtime_box),
            Create(cpu_box),
            Create(thread0),
            Create(thread1),
            Create(thread2)
        )
        self.wait(1)

        # --- Phase 1: Initialization & Spawn T1 ---
        phase1_title = Text("Phase 1: Init & Spawn T1", font_size=24, color=BLACK).to_edge(DOWN) # Adjust color if background changes
        self.play(Write(phase1_title))

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

        # 1.2 Show runtime.spawn(|| { /* T1 code */ });
        spawn_t1_code = Code(
            code_string="runtime.spawn(|| {\n  // T1 function body...\n});",
            language="rust",
            formatter_style="default",
            paragraph_config={"font_size": 18}
        ).next_to(runtime_box, DOWN, buff=0.3).align_to(runtime_box, LEFT)
        self.play(FadeIn(spawn_t1_code))

        # Highlight T1 being chosen
        self.play(Indicate(thread1.box, color=YELLOW, scale_factor=1.1))

        # 1.3 Setup T1's stack
        stack_setup_title = Text("Setting up T1 Stack", font_size=18, color=BLACK).next_to(thread1.stack_box, UP, buff=0.2)
        self.play(Write(stack_setup_title))

        # Simulate placing items onto T1's stack
        stack_top = thread1.get_stack_top_pos()
        stack_bottom = thread1.get_stack_bottom_pos()

        # Represent stack items (Guard, Skip, Func1)
        guard_addr = Text("G (Guard)", font_size=12, color=STACK_ITEM_COLOR).move_to(stack_top + DOWN * 0.2)
        skip_addr = Text("S (Skip)", font_size=12, color=STACK_ITEM_COLOR).next_to(guard_addr, DOWN, buff=0.1)
        func1_addr = Text("F1 (T1 Func)", font_size=12, color=STACK_ITEM_COLOR).next_to(skip_addr, DOWN, buff=0.1)

        # Simulate RSP pointing to F1's location on stack
        t1_initial_rsp_val = f"0x...{thread1.thread_id}F1" # Simulated address
        rsp_pointer = Arrow(
            start=thread1.ctx_registers[0].get_right() + RIGHT*0.1, # Start from ctx rsp label
            end=func1_addr.get_left() + LEFT*0.1,
            buff=0.1, stroke_width=2, max_tip_length_to_length_ratio=0.1, color=POINTER_COLOR
        )
        rsp_pointer_label = Text("ctx.rsp", font_size=12, color=POINTER_COLOR).next_to(rsp_pointer, UP, buff=0.05)

        self.play(
            FadeIn(guard_addr, shift=DOWN*0.2),
            FadeIn(skip_addr, shift=DOWN*0.2),
            FadeIn(func1_addr, shift=DOWN*0.2),
            run_time=1.5
        )
        self.play(
            thread1.update_ctx({"rsp": t1_initial_rsp_val}), # Update ctx display
            Create(rsp_pointer),
            Write(rsp_pointer_label)
        )
        self.wait(1)

        # 1.4 Change T1 state to Ready
        self.play(thread1.update_state("Ready"))
        self.wait(1)

        # Cleanup Phase 1 visuals
        self.play(
            FadeOut(spawn_t1_code),
            FadeOut(stack_setup_title),
            FadeOut(guard_addr),
            FadeOut(skip_addr),
            FadeOut(func1_addr),
            FadeOut(rsp_pointer),
            FadeOut(rsp_pointer_label),
            FadeOut(phase1_title)
        )
        self.wait(0.5)

        # --- Phase 2: Spawn T2 ---
        phase2_title = Text("Phase 2: Spawn T2", font_size=24, color=BLACK).to_edge(DOWN)
        self.play(Write(phase2_title))

        # 2.1 Show runtime.spawn(|| { /* T2 code */ });
        spawn_t2_code = Code(
            code_string="runtime.spawn(|| {\n  // T2 function body...\n});",
            language="rust",
            formatter_style="default",
            paragraph_config={"font_size": 18}
        ).next_to(runtime_box, DOWN, buff=0.3).align_to(runtime_box, LEFT)
        self.play(FadeIn(spawn_t2_code))

        # Highlight T2 being chosen
        self.play(Indicate(thread2.box, color=YELLOW, scale_factor=1.1))

        # 2.2 Setup T2's stack
        stack_setup_title_t2 = Text("Setting up T2 Stack", font_size=18, color=BLACK).next_to(thread2.stack_box, UP, buff=0.2)
        self.play(Write(stack_setup_title_t2))

        # Simulate placing items onto T2's stack
        stack_top_t2 = thread2.get_stack_top_pos()
        guard_addr_t2 = Text("G (Guard)", font_size=12, color=STACK_ITEM_COLOR).move_to(stack_top_t2 + DOWN * 0.2)
        skip_addr_t2 = Text("S (Skip)", font_size=12, color=STACK_ITEM_COLOR).next_to(guard_addr_t2, DOWN, buff=0.1)
        func2_addr = Text("F2 (T2 Func)", font_size=12, color=STACK_ITEM_COLOR).next_to(skip_addr_t2, DOWN, buff=0.1)

        # Simulate RSP pointing to F2's location on stack
        t2_initial_rsp_val = f"0x...{thread2.thread_id}F2" # Simulated address
        rsp_pointer_t2 = Arrow(
            start=thread2.ctx_registers[0].get_right() + RIGHT*0.1,
            end=func2_addr.get_left() + LEFT*0.1,
            buff=0.1, stroke_width=2, max_tip_length_to_length_ratio=0.1, color=POINTER_COLOR
        )
        rsp_pointer_label_t2 = Text("ctx.rsp", font_size=12, color=POINTER_COLOR).next_to(rsp_pointer_t2, UP, buff=0.05)

        self.play(
            FadeIn(guard_addr_t2, shift=DOWN*0.2),
            FadeIn(skip_addr_t2, shift=DOWN*0.2),
            FadeIn(func2_addr, shift=DOWN*0.2),
            run_time=1.5
        )
        self.play(
            thread2.update_ctx({"rsp": t2_initial_rsp_val}), # Update ctx display
            Create(rsp_pointer_t2),
            Write(rsp_pointer_label_t2)
        )
        self.wait(1)

        # 2.3 Change T2 state to Ready
        self.play(thread2.update_state("Ready"))
        self.wait(1)

        # Cleanup Phase 2 visuals
        self.play(
            FadeOut(spawn_t2_code),
            FadeOut(stack_setup_title_t2),
            FadeOut(guard_addr_t2),
            FadeOut(skip_addr_t2),
            FadeOut(func2_addr),
            FadeOut(rsp_pointer_t2),
            FadeOut(rsp_pointer_label_t2),
            FadeOut(phase2_title)
        )
        self.wait(0.5)

        # --- Phase 3: Run & First Yield (T0 -> T1) ---
        phase3_title = Text("Phase 3: Yield T0 -> T1", font_size=24, color=BLACK).to_edge(DOWN)
        self.play(Write(phase3_title))

        # 3.1 Show runtime.run() leading to t_yield()
        run_code = Code(
            code_string="runtime.run() {\n  // loop {\n    t_yield();\n  // }\n}",
            language="rust", formatter_style="default", paragraph_config={"font_size": 18}
        ).next_to(runtime_box, DOWN, buff=0.3).align_to(runtime_box, LEFT)
        yield_code = Code(
            code_string="t_yield() {\n  // 1. Find next ready thread\n  // 2. Switch context\n}",
            language="rust", formatter_style="default", paragraph_config={"font_size": 18}
        ).next_to(run_code, RIGHT, buff=0.5)

        self.play(FadeIn(run_code))
        self.wait(0.5)
        self.play(FadeIn(yield_code))
        self.wait(1)

        # 3.2 Scheduling: Find T1
        # Highlight current T0, then search and highlight T1
        self.play(Indicate(thread0.box, color=GREEN)) # Indicate current
        self.wait(0.5)
        # Simulate search (can add arrows later if needed)
        self.play(Indicate(thread1.box, color=YELLOW)) # Indicate found ready thread
        self.wait(1)

        # 3.3 State Transitions & Runtime Update
        self.play(
            thread0.update_state("Ready"), # T0 becomes Ready
            thread1.update_state("Running"), # T1 becomes Running
            runtime_box.update_current("1")  # Runtime points to T1
        )
        self.wait(1)

        # 3.4 Prepare for switch: Show switch call
        switch_code = Code(
            code_string="// Get old_ctx (T0), new_ctx (T1)\nswitch(old_ctx, new_ctx);",
            language="rust", formatter_style="default", paragraph_config={"font_size": 18}
        ).next_to(yield_code, RIGHT, buff=0.5)
        self.play(FadeIn(switch_code))
        self.wait(1)

        # 3.5 Context Switch Animation (T0 -> T1)
        switch_title = Text("Context Switch: T0 -> T1", font_size=18, color=BLACK).next_to(cpu_box, DOWN, buff=0.3)
        self.play(Write(switch_title))

        # Simulate saving T0's context (Simplified: just show arrows)
        # Assume some arbitrary values in CPU for T0
        t0_runtime_regs = {"rsp": "0x...T0SP", "rip": "0x...T0IP", "rbx": "0xT0BX", "rbp": "0xT0BP", "r12": "0xT012"}
        self.play(cpu_box.update_registers(t0_runtime_regs))
        self.wait(0.5)

        save_arrows = VGroup()
        for i, reg_label in enumerate(cpu_box.registers):
            if i < len(thread0.ctx_registers): # Only map visible registers
                 arrow = Arrow(
                     start=reg_label.get_right(),
                     end=thread0.ctx_registers[i].get_left(),
                     buff=0.1, stroke_width=1, max_tip_length_to_length_ratio=0.1, color=ORANGE
                 )
                 save_arrows.add(arrow)

        save_text = Text("Save T0 Ctx", font_size=14, color=ORANGE).next_to(save_arrows, LEFT)
        self.play(Create(save_arrows), Write(save_text))
        self.play(thread0.update_ctx(t0_runtime_regs)) # Update T0's ctx display
        self.wait(1)
        self.play(FadeOut(save_arrows), FadeOut(save_text))

        # Simulate loading T1's context
        # T1's context has the initial RSP we set, RIP is implicitly the function start (F1)
        t1_initial_ctx = {"rsp": t1_initial_rsp_val, "rip": f"0x...F1", "rbx": "0x0", "rbp": "0x0", "r12": "0x0"} # Initial values are often 0

        load_arrows = VGroup()
        for i, reg_label in enumerate(cpu_box.registers):
             if i < len(thread1.ctx_registers):
                 arrow = Arrow(
                     start=thread1.ctx_registers[i].get_right(),
                     end=reg_label.get_left(),
                     buff=0.1, stroke_width=1, max_tip_length_to_length_ratio=0.1, color=GREEN
                 )
                 load_arrows.add(arrow)

        load_text = Text("Load T1 Ctx", font_size=14, color=GREEN).next_to(load_arrows, RIGHT)
        self.play(Create(load_arrows), Write(load_text))
        self.play(cpu_box.update_registers(t1_initial_ctx)) # Update CPU display
        self.wait(1)
        self.play(FadeOut(load_arrows), FadeOut(load_text))

        # 3.6 Jump to T1 code (via ret)
        # Highlight RIP change and maybe show a simplified T1 code snippet
        # Use local variable t1_code
        t1_code = Code(
            code_string="fn thread1_func() {\n  println!(\"T1 running\");\n  // ... yield ...\n}",
            language="rust", formatter_style="default", paragraph_config={"font_size": 16}
        ).next_to(thread1, DOWN, buff=0.3)

        rip_indicator = SurroundingRectangle(cpu_box.registers[1], buff=0.05, color=RED) # Highlight RIP register
        control_flow_arrow = Arrow(
            start=cpu_box.box.get_bottom(),
            end=t1_code.get_top(), # Use local t1_code
            color=RED, stroke_width=3
        )
        self.control_flow_arrow = control_flow_arrow # Store arrow reference if needed across phases

        self.play(Create(rip_indicator))
        self.wait(0.5)
        self.play(FadeIn(t1_code, shift=UP), Create(control_flow_arrow)) # Use local t1_code
        self.wait(1)

        # Cleanup Phase 3 visuals
        self.play(
            FadeOut(run_code),
            FadeOut(yield_code),
            FadeOut(switch_code),
            FadeOut(switch_title),
            FadeOut(rip_indicator),
            # Keep t1_code and control_flow_arrow visible for Phase 4
            FadeOut(phase3_title)
        )
        self.wait(0.5)

        # --- Phase 4: T1 Executes & Yields (T1 -> T2) ---
        phase4_title = Text("Phase 4: Yield T1 -> T2", font_size=24, color=BLACK).to_edge(DOWN)
        self.play(Write(phase4_title))

        # 4.1 T1 code execution (briefly)
        # Simulate some work, maybe slight RSP change in CPU if desired
        t1_running_regs = t1_initial_ctx.copy()
        t1_running_regs["rsp"] = "0x...T1SP_mid" # Simulate stack pointer moving
        t1_running_regs["rip"] = "0x...T1_yield" # Simulate RIP advancing
        self.play(cpu_box.update_registers(t1_running_regs), run_time=0.5)
        # Highlight the yield line in T1's code
        # Assuming the yield call is the last line shown in the snippet
        # Access the last line mobject using index [-1] on local t1_code
        yield_line_highlight = SurroundingRectangle(t1_code[-1], color=YELLOW, buff=0.05)
        self.play(Create(yield_line_highlight))
        self.wait(1)

        # 4.2 Enter t_yield again
        self.play(FadeIn(yield_code)) # Re-show yield code logic
        self.wait(1)

        # 4.3 Scheduling: Find T2
        self.play(Indicate(thread1.box, color=GREEN)) # Indicate current T1
        self.wait(0.5)
        self.play(Indicate(thread2.box, color=YELLOW)) # Indicate found ready T2
        self.wait(1)

        # 4.4 State Transitions & Runtime Update
        self.play(
            thread1.update_state("Ready"),   # T1 becomes Ready
            thread2.update_state("Running"), # T2 becomes Running
            runtime_box.update_current("2")    # Runtime points to T2
        )
        self.wait(1)

        # 4.5 Prepare for switch: Show switch call again
        self.play(FadeIn(switch_code))
        self.wait(1)

        # 4.6 Context Switch Animation (T1 -> T2)
        switch_title_2 = Text("Context Switch: T1 -> T2", font_size=18, color=BLACK).next_to(cpu_box, DOWN, buff=0.3)
        self.play(Transform(switch_title, switch_title_2)) # Reuse the title mobject

        # Save T1's current context (values from t1_running_regs)
        save_arrows_t1 = VGroup()
        for i, reg_label in enumerate(cpu_box.registers):
            if i < len(thread1.ctx_registers):
                 arrow = Arrow(start=reg_label.get_right(), end=thread1.ctx_registers[i].get_left(), buff=0.1, stroke_width=1, max_tip_length_to_length_ratio=0.1, color=ORANGE)
                 save_arrows_t1.add(arrow)
        save_text_t1 = Text("Save T1 Ctx", font_size=14, color=ORANGE).next_to(save_arrows_t1, LEFT)

        self.play(Create(save_arrows_t1), Write(save_text_t1))
        self.play(thread1.update_ctx(t1_running_regs)) # Update T1's ctx display with current CPU state
        self.wait(1)
        self.play(FadeOut(save_arrows_t1), FadeOut(save_text_t1))

        # Load T2's initial context
        t2_initial_ctx = {"rsp": t2_initial_rsp_val, "rip": f"0x...F2", "rbx": "0x0", "rbp": "0x0", "r12": "0x0"}

        load_arrows_t2 = VGroup()
        for i, reg_label in enumerate(cpu_box.registers):
             if i < len(thread2.ctx_registers):
                 arrow = Arrow(start=thread2.ctx_registers[i].get_right(), end=reg_label.get_left(), buff=0.1, stroke_width=1, max_tip_length_to_length_ratio=0.1, color=GREEN)
                 load_arrows_t2.add(arrow)
        load_text_t2 = Text("Load T2 Ctx", font_size=14, color=GREEN).next_to(load_arrows_t2, RIGHT)

        self.play(Create(load_arrows_t2), Write(load_text_t2))
        self.play(cpu_box.update_registers(t2_initial_ctx)) # Update CPU display with T2's initial state
        self.wait(1)
        self.play(FadeOut(load_arrows_t2), FadeOut(load_text_t2))

        # 4.7 Jump to T2 code
        # Use local variable t2_code
        t2_code = Code(
            code_string="fn thread2_func() {\n  println!(\"T2 running\");\n  // ... yield ...\n}",
            language="rust", formatter_style="default", paragraph_config={"font_size": 16}
        ).next_to(thread2, DOWN, buff=0.3)

        # Reuse indicator and arrow (use self.control_flow_arrow)
        self.play(Indicate(cpu_box.registers[1])) # Highlight RIP again
        self.play(
            FadeOut(t1_code), # Fade out local t1_code
            FadeOut(yield_line_highlight),
            FadeIn(t2_code, shift=UP), # Fade in local t2_code
            Transform(self.control_flow_arrow, Arrow(start=cpu_box.box.get_bottom(), end=t2_code.get_top(), color=RED, stroke_width=3))
        )
        self.wait(1)

        # Cleanup Phase 4 visuals
        self.play(
            FadeOut(yield_code),
            FadeOut(switch_code),
            FadeOut(switch_title), # Fades out the transformed title
            # Keep t2_code and self.control_flow_arrow visible for Phase 5
            FadeOut(phase4_title)
        )
        self.wait(0.5)

        # --- Phase 5: T2 Executes & Yields (T2 -> T1) ---
        phase5_title = Text("Phase 5: Yield T2 -> T1", font_size=24, color=BLACK).to_edge(DOWN)
        self.play(Write(phase5_title))

        # 5.1 T2 code execution
        # Use local t2_code from Phase 4
        t2_running_regs = t2_initial_ctx.copy()
        t2_running_regs["rsp"] = "0x...T2SP_mid"
        t2_running_regs["rip"] = "0x...T2_yield"
        self.play(cpu_box.update_registers(t2_running_regs), run_time=0.5)
        # Access the last line mobject using index [-1] on local t2_code
        yield_line_highlight_t2 = SurroundingRectangle(t2_code[-1], color=YELLOW, buff=0.05)
        self.play(Create(yield_line_highlight_t2))
        self.wait(1)

        # 5.2 Enter t_yield again
        self.play(FadeIn(yield_code))
        self.wait(1)

        # 5.3 Scheduling: Find T1
        self.play(Indicate(thread2.box, color=GREEN)) # Indicate current T2
        self.wait(0.5)
        self.play(Indicate(thread1.box, color=YELLOW)) # Indicate found ready T1
        self.wait(1)

        # 5.4 State Transitions & Runtime Update
        self.play(
            thread2.update_state("Ready"),   # T2 becomes Ready
            thread1.update_state("Running"), # T1 becomes Running again
            runtime_box.update_current("1")    # Runtime points back to T1
        )
        self.wait(1)

        # 5.5 Prepare for switch: Show switch call again
        self.play(FadeIn(switch_code))
        self.wait(1)

        # 5.6 Context Switch Animation (T2 -> T1)
        switch_title_3 = Text("Context Switch: T2 -> T1", font_size=18, color=BLACK).next_to(cpu_box, DOWN, buff=0.3)
        # We need the previous switch_title mobject to transform from. Let's assume it was stored or recreate if necessary.
        # For simplicity, let's just create a new one if the old reference is lost.
        # If switch_title was faded out, we need to Write it again or Transform from an existing one.
        # Let's assume switch_title is still available from Phase 4 cleanup or recreate it.
        # Recreating for safety:
        switch_title = Text("Context Switch: T1 -> T2", font_size=18, color=BLACK).next_to(cpu_box, DOWN, buff=0.3) # Recreate previous state
        self.add(switch_title) # Add it without animation if it was faded
        self.play(Transform(switch_title, switch_title_3))

        # Save T2's current context
        save_arrows_t2 = VGroup()
        for i, reg_label in enumerate(cpu_box.registers):
            if i < len(thread2.ctx_registers):
                 arrow = Arrow(start=reg_label.get_right(), end=thread2.ctx_registers[i].get_left(), buff=0.1, stroke_width=1, max_tip_length_to_length_ratio=0.1, color=ORANGE)
                 save_arrows_t2.add(arrow)
        save_text_t2 = Text("Save T2 Ctx", font_size=14, color=ORANGE).next_to(save_arrows_t2, LEFT)

        self.play(Create(save_arrows_t2), Write(save_text_t2))
        self.play(thread2.update_ctx(t2_running_regs)) # Update T2's ctx display
        self.wait(1)
        self.play(FadeOut(save_arrows_t2), FadeOut(save_text_t2))

        # Load T1's *PREVIOUSLY SAVED* context (from t1_running_regs)
        t1_saved_ctx = t1_running_regs # This holds the state T1 was in when it yielded

        load_arrows_t1_resume = VGroup()
        for i, reg_label in enumerate(cpu_box.registers):
             if i < len(thread1.ctx_registers):
                 arrow = Arrow(start=thread1.ctx_registers[i].get_right(), end=reg_label.get_left(), buff=0.1, stroke_width=1, max_tip_length_to_length_ratio=0.1, color=GREEN)
                 load_arrows_t1_resume.add(arrow)
        load_text_t1_resume = Text("Load T1 Ctx (Resume)", font_size=14, color=GREEN).next_to(load_arrows_t1_resume, RIGHT)

        self.play(Create(load_arrows_t1_resume), Write(load_text_t1_resume))
        self.play(cpu_box.update_registers(t1_saved_ctx)) # Update CPU with T1's saved state
        self.wait(1)
        self.play(FadeOut(load_arrows_t1_resume), FadeOut(load_text_t1_resume))

        # 5.7 Jump back to T1 code (resume execution)
        # Recreate T1 code snippet as a local variable
        t1_code_resume = Code(
            code_string="fn thread1_func() {\n  println!(\"T1 running\");\n  // ... yield ...\n}",
            language="rust", formatter_style="default", paragraph_config={"font_size": 16}
        ).next_to(thread1, DOWN, buff=0.3)

        self.play(Indicate(cpu_box.registers[1])) # Highlight RIP again
        self.play(
            FadeOut(t2_code), # Remove local t2_code
            FadeOut(yield_line_highlight_t2),
            FadeIn(t1_code_resume, shift=UP), # Bring back T1 code (local)
            Transform(self.control_flow_arrow, Arrow(start=cpu_box.box.get_bottom(), end=t1_code_resume.get_top(), color=RED, stroke_width=3)) # Point arrow back to T1 (local)
        )
        # Highlight the instruction *after* yield in T1's code (conceptual)
        # Access the third line mobject (index 2) on local t1_code_resume
        resume_highlight = SurroundingRectangle(t1_code_resume[2], color=GREEN_C, buff=0.05) # Highlight line after yield
        self.play(Create(resume_highlight))
        self.wait(1)


        # Cleanup Phase 5 visuals
        self.play(
            FadeOut(yield_code),
            FadeOut(switch_code),
            FadeOut(switch_title),
            FadeOut(resume_highlight),
            # Keep t1_code_resume and self.control_flow_arrow for next phase
            FadeOut(phase5_title)
        )
        self.wait(0.5)

        # --- Phase 6: T1 Finishes & Enters Guard ---
        phase6_title = Text("Phase 6: T1 Finishes -> Guard", font_size=24, color=BLACK).to_edge(DOWN)
        self.play(Write(phase6_title))

        # 6.1 T1 function finishes (conceptual 'ret')
        # Remove T1's code snippet (use local t1_code_resume from Phase 5), show 'ret' conceptually happening
        ret_text = Text("T1 func returns (ret)", font_size=16, color=CODE_COLOR).move_to(t1_code_resume)
        self.play(FadeOut(t1_code_resume), FadeIn(ret_text))
        self.wait(1)

        # 6.2 CPU 'ret' loads Guard address from T1 stack
        # Highlight the Guard address on T1's stack (recreate if faded)
        guard_addr_t1_vis = Text("G (Guard)", font_size=12, color=STACK_ITEM_COLOR).move_to(thread1.get_stack_top_pos() + DOWN * 0.2) # Recreate visual
        self.add(guard_addr_t1_vis) # Add if faded previously

        # Animate popping Guard address to RIP
        pop_arrow = Arrow(
            start=guard_addr_t1_vis.get_top(),
            end=cpu_box.registers[1].get_bottom(), # Point towards RIP
            buff=0.1, stroke_width=2, color=PURPLE
        )
        pop_text = Text("ret pops G", font_size=14, color=PURPLE).next_to(pop_arrow, LEFT)

        # Update CPU RIP to Guard address
        t1_guard_regs = cpu_box.registers.copy() # Get current CPU state (from T1 resume)
        t1_guard_regs_dict = {"rip": "0x...Guard"} # Only update RIP conceptually
        # We need the actual register values from the end of phase 5
        t1_saved_ctx_from_p5 = t1_saved_ctx # Reuse the dict from phase 5 load
        t1_saved_ctx_from_p5["rip"] = "0x...Guard" # Update RIP

        self.play(Indicate(guard_addr_t1_vis), Create(pop_arrow), Write(pop_text))
        self.wait(0.5)
        self.play(cpu_box.update_registers(t1_saved_ctx_from_p5)) # Update CPU RIP
        self.play(FadeOut(pop_arrow), FadeOut(pop_text), FadeOut(ret_text), FadeOut(guard_addr_t1_vis))
        self.wait(1)

        # 6.3 CPU executes Guard function
        guard_code = Code(
            code_string="fn guard() {\n  // Set state = Available\n  t_yield();\n}",
            language="rust", formatter_style="default", paragraph_config={"font_size": 16}
        ).next_to(thread1, DOWN, buff=0.3) # Place near T1

        self.play(
            Transform(self.control_flow_arrow, Arrow(start=cpu_box.box.get_bottom(), end=guard_code.get_top(), color=RED, stroke_width=3)), # Point to guard code
            FadeIn(guard_code)
        )
        self.wait(1)

        # 6.4 Guard sets T1 state to Available
        self.play(thread1.update_state("Available"))
        self.wait(1)

        # 6.5 Guard calls t_yield()
        # Highlight yield in guard code
        # Access the last line mobject using index [-1]
        guard_yield_highlight = SurroundingRectangle(guard_code[-1], color=YELLOW, buff=0.05)
        self.play(Create(guard_yield_highlight))
        self.play(FadeIn(yield_code)) # Show yield logic again
        self.wait(1)

        # 6.6 Scheduling: Find T2 (only T2 is Ready)
        self.play(Indicate(thread1.box, color=GREEN)) # Indicate current T1 (in guard)
        self.wait(0.5)
        self.play(Indicate(thread2.box, color=YELLOW)) # Indicate found ready T2
        self.wait(1)

        # 6.7 State Transitions & Runtime Update
        # T1 remains Available, T2 becomes Running
        self.play(
            # thread1 state already Available
            thread2.update_state("Running"),
            runtime_box.update_current("2")
        )
        self.wait(1)

        # 6.8 Prepare for switch: Show switch call again
        self.play(FadeIn(switch_code))
        self.wait(1)

        # 6.9 Context Switch Animation (T1 [Guard] -> T2 [Resume])
        switch_title_4 = Text("Context Switch: T1(Guard) -> T2", font_size=18, color=BLACK).next_to(cpu_box, DOWN, buff=0.3)
        self.play(Transform(switch_title, switch_title_4)) # Transform from previous title

        # Save T1's context (while in guard calling yield)
        t1_guard_yield_regs = t1_saved_ctx_from_p5.copy() # CPU state is currently Guard's RIP
        t1_guard_yield_regs["rip"] = "0x...GuardYield" # RIP is after yield call in guard

        save_arrows_t1_guard = VGroup()
        # ... (create arrows from CPU to T1 ctx) ...
        for i, reg_label in enumerate(cpu_box.registers):
             if i < len(thread1.ctx_registers):
                  arrow = Arrow(start=reg_label.get_right(), end=thread1.ctx_registers[i].get_left(), buff=0.1, stroke_width=1, max_tip_length_to_length_ratio=0.1, color=ORANGE)
                  save_arrows_t1_guard.add(arrow)
        save_text_t1_guard = Text("Save T1 Guard Ctx", font_size=14, color=ORANGE).next_to(save_arrows_t1_guard, LEFT)

        self.play(Create(save_arrows_t1_guard), Write(save_text_t1_guard))
        self.play(thread1.update_ctx(t1_guard_yield_regs))
        self.wait(1)
        self.play(FadeOut(save_arrows_t1_guard), FadeOut(save_text_t1_guard))

        # Load T2's previously saved context (from t2_running_regs)
        t2_saved_ctx = t2_running_regs # This holds the state T2 was in when it yielded

        load_arrows_t2_resume = VGroup()
        # ... (create arrows from T2 ctx to CPU) ...
        for i, reg_label in enumerate(cpu_box.registers):
              if i < len(thread2.ctx_registers):
                  arrow = Arrow(start=thread2.ctx_registers[i].get_right(), end=reg_label.get_left(), buff=0.1, stroke_width=1, max_tip_length_to_length_ratio=0.1, color=GREEN)
                  load_arrows_t2_resume.add(arrow)
        load_text_t2_resume = Text("Load T2 Ctx (Resume)", font_size=14, color=GREEN).next_to(load_arrows_t2_resume, RIGHT)

        self.play(Create(load_arrows_t2_resume), Write(load_text_t2_resume))
        self.play(cpu_box.update_registers(t2_saved_ctx)) # Update CPU with T2's saved state
        self.wait(1)
        self.play(FadeOut(load_arrows_t2_resume), FadeOut(load_text_t2_resume))

        # 6.10 Jump back to T2 code (resume execution)
        # Use local t2_code from Phase 4
        self.play(Indicate(cpu_box.registers[1])) # Highlight RIP
        self.play(
            FadeOut(guard_code),
            FadeOut(guard_yield_highlight),
            FadeIn(t2_code, shift=UP), # Bring back local t2_code
            Transform(self.control_flow_arrow, Arrow(start=cpu_box.box.get_bottom(), end=t2_code.get_top(), color=RED, stroke_width=3)) # Point arrow back to local t2_code
        )
        # Highlight the instruction *after* yield in T2's code
        # Access the third line mobject (index 2) on local t2_code
        resume_highlight_t2 = SurroundingRectangle(t2_code[2], color=GREEN_C, buff=0.05)
        self.play(Create(resume_highlight_t2))
        self.wait(1)

        # Cleanup Phase 6 visuals
        self.play(
            FadeOut(yield_code),
            FadeOut(switch_code),
            FadeOut(switch_title),
            FadeOut(resume_highlight_t2),
            # Keep T2 code snippet and arrow
            FadeOut(phase6_title)
        )
        self.wait(0.5)

        # --- Phase 7: T2 Finishes & Runtime Ends ---
        phase7_title = Text("Phase 7: T2 Finishes & Runtime Ends", font_size=24, color=BLACK).to_edge(DOWN)
        self.play(Write(phase7_title))

        # 7.1 T2 function finishes (conceptual 'ret')
        # Use local t2_code from Phase 4/6
        ret_text_t2 = Text("T2 func returns (ret)", font_size=16, color=CODE_COLOR).move_to(t2_code)
        self.play(FadeOut(t2_code), FadeIn(ret_text_t2))
        self.wait(1)

        # 7.2 CPU 'ret' loads Guard address from T2 stack
        guard_addr_t2_vis = Text("G (Guard)", font_size=12, color=STACK_ITEM_COLOR).move_to(thread2.get_stack_top_pos() + DOWN * 0.2) # Recreate visual
        self.add(guard_addr_t2_vis) # Add if faded previously

        pop_arrow_t2 = Arrow(start=guard_addr_t2_vis.get_top(), end=cpu_box.registers[1].get_bottom(), buff=0.1, stroke_width=2, color=PURPLE)
        pop_text_t2 = Text("ret pops G", font_size=14, color=PURPLE).next_to(pop_arrow_t2, LEFT)

        # Update CPU RIP to Guard address (based on T2's last saved state)
        t2_saved_ctx_from_p6 = t2_saved_ctx # Reuse from phase 6 load
        t2_saved_ctx_from_p6["rip"] = "0x...Guard" # Update RIP

        self.play(Indicate(guard_addr_t2_vis), Create(pop_arrow_t2), Write(pop_text_t2))
        self.wait(0.5)
        self.play(cpu_box.update_registers(t2_saved_ctx_from_p6)) # Update CPU RIP
        self.play(FadeOut(pop_arrow_t2), FadeOut(pop_text_t2), FadeOut(ret_text_t2), FadeOut(guard_addr_t2_vis))
        self.wait(1)

        # 7.3 CPU executes Guard function for T2
        # Reuse guard_code mobject, move it near T2
        self.play(
            Transform(self.control_flow_arrow, Arrow(start=cpu_box.box.get_bottom(), end=guard_code.get_top(), color=RED, stroke_width=3)), # Point to guard code
            guard_code.animate.next_to(thread2, DOWN, buff=0.3) # Move guard code visual
        )
        self.play(FadeIn(guard_code)) # Ensure it's visible
        self.wait(1)

        # 7.4 Guard sets T2 state to Available
        self.play(thread2.update_state("Available"))
        self.wait(1)

        # 7.5 Guard calls t_yield()
        self.play(Create(guard_yield_highlight)) # Reuse highlight
        self.play(FadeIn(yield_code))
        self.wait(1)

        # 7.6 Scheduling: Find T0 (only T0 is Ready)
        self.play(Indicate(thread2.box, color=GREEN)) # Indicate current T2 (in guard)
        self.wait(0.5)
        # Simulate search - finds no Ready threads other than T0
        no_ready_text = Text("No other Ready threads found", font_size=16, color=RED).next_to(yield_code, DOWN)
        self.play(Write(no_ready_text))
        self.wait(1)
        self.play(Indicate(thread0.box, color=YELLOW)) # Indicate switching back to T0
        self.wait(1)

        # 7.7 State Transitions & Runtime Update
        # T2 remains Available, T0 becomes Running again
        self.play(
            thread0.update_state("Running"),
            runtime_box.update_current("0")
        )
        self.wait(1)

        # 7.8 Prepare for switch: Show switch call again
        self.play(FadeIn(switch_code))
        self.wait(1)

        # 7.9 Context Switch Animation (T2 [Guard] -> T0 [Resume])
        switch_title_5 = Text("Context Switch: T2(Guard) -> T0", font_size=18, color=BLACK).next_to(cpu_box, DOWN, buff=0.3)
        self.play(Transform(switch_title, switch_title_5)) # Transform from previous title

        # Save T2's context (while in guard calling yield)
        t2_guard_yield_regs = t2_saved_ctx_from_p6.copy()
        t2_guard_yield_regs["rip"] = "0x...GuardYield"

        save_arrows_t2_guard = VGroup()
        # ... (create arrows CPU -> T2 ctx) ...
        for i, reg_label in enumerate(cpu_box.registers):
             if i < len(thread2.ctx_registers):
                  arrow = Arrow(start=reg_label.get_right(), end=thread2.ctx_registers[i].get_left(), buff=0.1, stroke_width=1, max_tip_length_to_length_ratio=0.1, color=ORANGE)
                  save_arrows_t2_guard.add(arrow)
        save_text_t2_guard = Text("Save T2 Guard Ctx", font_size=14, color=ORANGE).next_to(save_arrows_t2_guard, LEFT)

        self.play(Create(save_arrows_t2_guard), Write(save_text_t2_guard))
        self.play(thread2.update_ctx(t2_guard_yield_regs))
        self.wait(1)
        self.play(FadeOut(save_arrows_t2_guard), FadeOut(save_text_t2_guard))

        # Load T0's previously saved context (from t0_runtime_regs in Phase 3)
        t0_saved_ctx = t0_runtime_regs

        load_arrows_t0_resume = VGroup()
        # ... (create arrows T0 ctx -> CPU) ...
        for i, reg_label in enumerate(cpu_box.registers):
              if i < len(thread0.ctx_registers):
                   arrow = Arrow(start=thread0.ctx_registers[i].get_right(), end=reg_label.get_left(), buff=0.1, stroke_width=1, max_tip_length_to_length_ratio=0.1, color=GREEN)
                   load_arrows_t0_resume.add(arrow)
        load_text_t0_resume = Text("Load T0 Ctx (Resume)", font_size=14, color=GREEN).next_to(load_arrows_t0_resume, RIGHT)

        self.play(Create(load_arrows_t0_resume), Write(load_text_t0_resume))
        self.play(cpu_box.update_registers(t0_saved_ctx)) # Update CPU with T0's saved state
        self.wait(1)
        self.play(FadeOut(load_arrows_t0_resume), FadeOut(load_text_t0_resume))

        # 7.10 Jump back to T0 (runtime loop)
        self.play(Indicate(cpu_box.registers[1])) # Highlight RIP
        # Point control flow back towards the runtime/main area conceptually
        self.play(
            FadeOut(guard_code),
            FadeOut(guard_yield_highlight),
            Transform(self.control_flow_arrow, Arrow(start=cpu_box.box.get_bottom(), end=runtime_box.box.get_left(), color=RED, stroke_width=3))
        )
        self.wait(1)

        # 7.11 Runtime loop ends
        runtime_ends_text = Text("runtime.run() loop finishes", font_size=18, color=RED).move_to(run_code)
        self.play(FadeOut(run_code), FadeIn(runtime_ends_text))
        self.wait(1)


        # Cleanup Phase 7 visuals
        self.play(
            FadeOut(yield_code),
            FadeOut(switch_code),
            FadeOut(switch_title),
            FadeOut(no_ready_text),
            FadeOut(runtime_ends_text),
            FadeOut(self.control_flow_arrow),
            FadeOut(phase7_title)
        )
        self.wait(0.5)


        # Final message
        final_text = Text("Animation Complete!", font_size=36, color=BLUE_COLOR)
        self.play(Write(final_text))
        self.wait(3)
