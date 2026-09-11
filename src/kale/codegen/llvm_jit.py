import ctypes
import llvmlite.binding as llvm

class LLVMJIT:
    """In-memory JIT execution engine using LLVM ORC/MCJIT."""
    _initialized = False

    def __init__(self, opt_level: int = 2):
        self.opt_level = opt_level
        self._init_llvm()

    @classmethod
    def _init_llvm(cls):
        if not cls._initialized:
            llvm.initialize_native_target()
            llvm.initialize_native_asmprinter()
            cls._initialized = True

    def run_ir(self, ir_text: str) -> int:
        """Parses, verifies, JIT-compiles, and executes the LLVM IR, returning the exit code."""
        mod = llvm.parse_assembly(ir_text)
        mod.verify()

        # Target machine with opt_level
        target = llvm.Target.from_default_triple()
        target_machine = target.create_target_machine(opt=self.opt_level)

        # Execution engine
        backing_mod = llvm.parse_assembly("")
        engine = llvm.create_mcjit_compiler(backing_mod, target_machine)
        engine.add_module(mod)
        engine.finalize_object()
        engine.run_static_constructors()

        # Run main()
        func_ptr = engine.get_function_address("main")
        if not func_ptr:
            raise RuntimeError("Entry function 'main' not found in compiled LLVM module.")

        c_main = ctypes.CFUNCTYPE(ctypes.c_int)(func_ptr)
        ret_val = c_main()
        return ret_val
