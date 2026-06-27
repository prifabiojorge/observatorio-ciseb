/**
 * Testes de autenticação para as rotas API — Fase 5+ (Supabase Auth).
 *
 * Fase 7 fix (auditoria Harness 2026-06-27): testes atualizados para refletir
 * que /api/findings/* agora usam Supabase Auth (cookies), não mais CRON_SECRET.
 * /api/cron/* continuam com CRON_SECRET.
 *
 * Mocks:
 * - @supabase/ssr createServerClient: simula sessão de usuário autenticado
 * - @supabase/supabase-js createClient: simula cliente Supabase
 */

// Mock do @supabase/ssr (usado por /api/findings/*)
const mockSession = { user: { id: 'user-uuid-123' } };
const mockSupabaseAuth = {
    auth: {
        getSession: jest.fn(),
    },
    from: jest.fn(() => ({
        select: jest.fn(() => ({
            eq: jest.fn(() => ({
                order: jest.fn(() => ({
                    limit: jest.fn(() => Promise.resolve({ data: [], error: null })),
                })),
            })),
            in: jest.fn(() => Promise.resolve({ data: [], error: null })),
        })),
        insert: jest.fn(() => Promise.resolve({ data: null, error: null })),
        update: jest.fn(() => ({
            eq: jest.fn(() => Promise.resolve({ data: null, error: null })),
        })),
    })),
};

jest.mock('@supabase/ssr', () => ({
    createServerClient: jest.fn(() => mockSupabaseAuth),
}));

// Mock do next/headers (cookies)
jest.mock('next/headers', () => ({
    cookies: jest.fn(() => ({
        getAll: jest.fn(() => []),
        set: jest.fn(),
    })),
}));

function makeRequest(headers: Record<string, string> = {}) {
    return {
        headers: {
            get: (name: string): string | null => headers[name] || null,
        },
        json: async () => ({}),
    };
}

describe('Rotas /api/cron/* — auth via CRON_SECRET (Fase 4+)', () => {
    const ORIGINAL_ENV = { ...process.env };

    beforeEach(() => {
        jest.resetModules();
        process.env = { ...ORIGINAL_ENV };
        process.env.CRON_SECRET = 'test-secret-123';
        process.env.SUPABASE_URL = 'https://fake.supabase.co';
        process.env.SUPABASE_SERVICE_ROLE_KEY = 'fake-service-role';
        process.env.RENDER_RUN_URL = 'https://fake.onrender.com/run';
        process.env.RENDER_DIGEST_URL = 'https://fake.onrender.com/digest';
    });

    afterAll(() => {
        process.env = ORIGINAL_ENV;
    });

    describe('GET /api/cron/collect', () => {
        it('retorna 401 sem Authorization', async () => {
            const { GET } = require('../app/api/cron/collect/route');
            const res = await GET(makeRequest());
            expect(res.status).toBe(401);
        });

        it('retorna 401 com token errado', async () => {
            const { GET } = require('../app/api/cron/collect/route');
            const res = await GET(makeRequest({ authorization: 'Bearer errado' }));
            expect(res.status).toBe(401);
        });
    });

    describe('GET /api/cron/digest', () => {
        it('retorna 401 sem Authorization', async () => {
            const { GET } = require('../app/api/cron/digest/route');
            const res = await GET(makeRequest());
            expect(res.status).toBe(401);
        });
    });
});

describe('Rotas /api/findings/* — auth via Supabase Auth (Fase 5+)', () => {
    const ORIGINAL_ENV = { ...process.env };

    beforeEach(() => {
        jest.resetModules();
        process.env = { ...ORIGINAL_ENV };
        process.env.NEXT_PUBLIC_SUPABASE_URL = 'https://fake.supabase.co';
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = 'fake-anon-key';
        // Reset session mock
        mockSupabaseAuth.auth.getSession.mockReset();
    });

    afterAll(() => {
        process.env = ORIGINAL_ENV;
    });

    describe('GET /api/findings/pending', () => {
        it('retorna 401 quando não há sessão', async () => {
            // Simula sessão ausente (middleware deveria bloquear, mas defesa em profundidade)
            mockSupabaseAuth.auth.getSession.mockResolvedValue({
                data: { session: null },
                error: null,
            });

            const { GET } = require('../app/api/findings/pending/route');
            const res = await GET(makeRequest());
            expect(res.status).toBe(401);
        });

        it('retorna 200 quando há sessão válida', async () => {
            mockSupabaseAuth.auth.getSession.mockResolvedValue({
                data: { session: mockSession },
                error: null,
            });

            const { GET } = require('../app/api/findings/pending/route');
            const res = await GET(makeRequest());
            // Como o mock retorna data: [], deve dar 200 com array vazio
            expect(res.status).toBe(200);
        });
    });

    describe('POST /api/findings/decide', () => {
        it('retorna 401 quando não há sessão', async () => {
            mockSupabaseAuth.auth.getSession.mockResolvedValue({
                data: { session: null },
                error: null,
            });

            const { POST } = require('../app/api/findings/decide/route');
            const req = {
                ...makeRequest(),
                json: async () => ({
                    id: '550e8400-e29b-41d4-a716-446655440000',
                    decision: 'approved',
                }),
            };
            const res = await POST(req);
            expect(res.status).toBe(401);
        });

        it('retorna 400 com id que não é UUID v4', async () => {
            mockSupabaseAuth.auth.getSession.mockResolvedValue({
                data: { session: mockSession },
                error: null,
            });

            const { POST } = require('../app/api/findings/decide/route');
            const req = {
                ...makeRequest(),
                json: async () => ({ id: 'nao-e-uuid', decision: 'approved' }),
            };
            const res = await POST(req);
            expect(res.status).toBe(400);
        });

        it('retorna 400 com decision inválida', async () => {
            mockSupabaseAuth.auth.getSession.mockResolvedValue({
                data: { session: mockSession },
                error: null,
            });

            const { POST } = require('../app/api/findings/decide/route');
            const req = {
                ...makeRequest(),
                json: async () => ({
                    id: '550e8400-e29b-41d4-a716-446655440000',
                    decision: 'maybe',
                }),
            };
            const res = await POST(req);
            expect(res.status).toBe(400);
        });

        it('retorna 200 com payload correto e sessão válida', async () => {
            mockSupabaseAuth.auth.getSession.mockResolvedValue({
                data: { session: mockSession },
                error: null,
            });

            const { POST } = require('../app/api/findings/decide/route');
            const req = {
                ...makeRequest(),
                json: async () => ({
                    id: '550e8400-e29b-41d4-a716-446655440000',
                    decision: 'approved',
                }),
            };
            const res = await POST(req);
            expect(res.status).toBe(200);
        });
    });
});
