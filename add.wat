(module
  (func $add (param $a i32) (param $b i32) (result i32)
    local.get $a
    local.get $b
    i32.add
  )
  (func $mul3 (param $x i32) (result i32)
    local.get $x
    i32.const 3
    i32.mul
  )
  (export "add" (func $add))
  (export "mul3" (func $mul3))
)