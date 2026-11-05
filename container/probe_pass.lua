-- Isolated lab-only diagnostic. No packets are modified or injected.
function zapret2_probe_pass(ctx, desync)
    DLOG("ZAPRET2_LUA_PROBE_INVOKED")
    return VERDICT_PASS
end
