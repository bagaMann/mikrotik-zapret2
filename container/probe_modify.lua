-- Controlled loopback-only payload replacement. Not for normal traffic.
function zapret2_probe_modify(ctx, desync)
    DLOG("ZAPRET2_LUA_MODIFY_INVOKED")
    if not desync.dis or not desync.dis.udp then
        return VERDICT_PASS
    end
    if desync.dis.payload ~= "zapret2-lua-original" then
        return VERDICT_PASS
    end
    desync.dis.payload = "zapret2-lua-modified"
    return VERDICT_MODIFY
end
