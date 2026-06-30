-- =============================================================================
-- seed.sql — Seed dos 6 pilares CISEB
-- =============================================================================
-- Esta seed NÃO é uma migração versionada (não segue o padrão NNN_).
-- Deve ser executada manualmente após as migrações 001-003 OU via
-- Supabase Dashboard → SQL Editor.
--
-- É idempotente: se os pilares já existirem (slug UNIQUE), a seed é
-- ignorada silenciosamente via ON CONFLICT DO NOTHING.
-- =============================================================================

INSERT INTO pillars (slug, name, description) VALUES

('ia', 'Inteligência Artificial',
 'Personalização de aprendizado, automação, assistentes educacionais. '
 'Foco: experiências pedagógicas em sala de aula.'),

('maker', 'Cultura Maker',
 'Criação prática com tecnologia e criatividade. '
 'Foco: metodologias de prototipagem adaptadas ao Brasil com restrição de recursos.'),

('digital', 'Cultura Digital',
 'Realidade Virtual e Aumentada para ensino. '
 'Foco: apps pedagógicas, soluções smartphone+cardboard, kits dev.'),

('tech_art', 'Tecnologia e Arte',
 'Jogos, animações, pensamento computacional. '
 'Foco: Scratch, p5.js, Processing, Godot, GDevelop, pixi.js.'),

('fabrication', 'Fabricação Digital',
 'Impressão 3D, cortadora a laser, prototipagem. '
 'Foco: modelos STL pedagógicos, segurança em makerspace escolar.'),

('robotics', 'Robótica Educacional',
 'Kits modernos: Arduino, micro:bit, RPi Pico, LEGO Spike, Mbot. '
 'Foco: competições, implementação em escolas públicas.')

ON CONFLICT (slug) DO NOTHING;

-- =============================================================================
-- VERIFICAÇÃO
-- =============================================================================
-- SELECT slug, name FROM pillars ORDER BY slug;
-- Esperado: 6 linhas (ia, maker, digital, tech_art, fabrication, robotics)
-- =============================================================================
-- FIM seed.sql
-- =============================================================================
