-- Пупырышки LEGO (D13): SurfaceType.Studs на верхней грани. Движок рисует их только на материале Plastic
-- (проверено в Studio: на SmoothPlastic не видно). Единственное место, где решается, как делать пупырышки.
-- Ни от чего не зависит.

local Studs = {}

function Studs.Apply(part: BasePart)
	part.BottomSurface = Enum.SurfaceType.Smooth
	if part.Material == Enum.Material.Plastic and part:IsA("Part") and part.Shape == Enum.PartType.Block then
		part.TopSurface = Enum.SurfaceType.Studs
	else
		part.TopSurface = Enum.SurfaceType.Smooth
	end
end

return Studs
