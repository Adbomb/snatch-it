-- Поверхности деталей (D13). Пупырышки теперь даёт MaterialVariant «LegoStuds» на всём Plastic
-- (см. shared/LegoMaterial), поэтому SurfaceType.Studs не используется: все грани гладкие.
-- Ни от чего не зависит.

local Studs = {}

function Studs.Apply(part: BasePart)
	part.TopSurface = Enum.SurfaceType.Smooth
	part.BottomSurface = Enum.SurfaceType.Smooth
end

return Studs
