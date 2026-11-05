-- Test only: drop the single selected loopback UDP packet.
function zapret2_probe_drop(ctx, desync)
    DLOG("ZAPRET2_LUA_DROP_INVOKED")
    return VERDICT_DROP
end
