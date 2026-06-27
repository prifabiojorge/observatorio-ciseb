/**
 * Testes de autenticação para as rotas API — Validação do patch #2.
 *
 * Estes testes mockam o cliente Supabase e validam APENAS a lógica de
 * autenticação (Bearer CRON_SECRET + fail-closed). Não testam a conexão
 * real com o banco.
 */

const mockSupabase = {
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

jest.mock('@supabase/supabase-js', () => ({
    createClient: jest.fn(() => mockSupabase),
}));

function makeRequest(headers = {}) {
    return {
        headers: {
            get: (name) => headers[name] || null,
        },
        json: async () => ({}),
    };
}

describe('Rotas API — validação de auth (patch #2)', () => {
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

    describe('GET /api/findings/pending', () => {
        it('retorna 401 sem header Authorization', async () => {
            const { GET } = require('../app/api/findings/pending/route');
            const res = await GET(makeRequest());
            expect(res.status).toBe(401);
            const body = await res.json();
            expect(body.error).toMatch(/Unauthorized/i);
        });

        it('retorna 401 com token errado', async () => {
            const { GET } = require('../app/api/findings/pending/route');
            const res = await GET(makeRequest({ authorization: 'Bearer token-errado' }));
            expect(res.status).toBe(401);
        });

        it('retorna 401 com Authorization malformado (sem Bearer)', async () => {
            const { GET } = require('../app/api/findings/pending/route');
            const res = await GET(makeRequest({ authorization: 'test-secret-123' }));
            expect(res.status).toBe(401);
        });

        it('retorna 401 com scheme diferente', async () => {
            const { GET } = require('../app/api/findings/pending/route');
            const res = await GET(makeRequest({ authorization: 'Basic test-secret-123' }));
            expect(res.status).toBe(401);
        });

        it('passa auth com Bearer + token correto', async () => {
            const { GET } = require('../app/api/findings/pending/route');
            const res = await GET(makeRequest({ authorization: 'Bearer test-secret-123' }));
            expect(res.status).toBe(200);
        });
    });

    describe('POST /api/findings/decide', () => {
        it('retorna 401 sem header Authorization', async () => {
            const { POST } = require('../app/api/findings/decide/route');
            const req = { ...makeRequest(), json: async () => ({ id: '550e8400-e29b-41d4-a716-446655440000', decision: 'approved' }) };
            const res = await POST(req);
            expect(res.status).toBe(401);
        });

        it('retorna 401 com token errado', async () => {
            const { POST } = require('../app/api/findings/decide/route');
            const req = {
                ...makeRequest({ authorization: 'Bearer errado' }),
                json: async () => ({ id: '550e8400-e29b-41d4-a716-446655440000', decision: 'approved' }),
            };
            const res = await POST(req);
            expect(res.status).toBe(401);
        });

        it('retorna 400 com id que não é UUID v4', async () => {
            const { POST } = require('../app/api/findings/decide/route');
            const req = {
                ...makeRequest({ authorization: 'Bearer test-secret-123' }),
                json: async () => ({ id: 'nao-e-uuid', decision: 'approved' }),
            };
            const res = await POST(req);
            expect(res.status).toBe(400);
            const body = await res.json();
            expect(body.error).toMatch(/UUID/i);
        });

        it('retorna 400 com decision inválida', async () => {
            const { POST } = require('../app/api/findings/decide/route');
            const req = {
                ...makeRequest({ authorization: 'Bearer test-secret-123' }),
                json: async () => ({ id: '550e8400-e29b-41d4-a716-446655440000', decision: 'maybe' }),
            };
            const res = await POST(req);
            expect(res.status).toBe(400);
        });

        it('passa auth e validação com payload correto', async () => {
            const { POST } = require('../app/api/findings/decide/route');
            const req = {
                ...makeRequest({ authorization: 'Bearer test-secret-123' }),
                json: async () => ({ id: '550e8400-e29b-41d4-a716-446655440000', decision: 'approved' }),
            };
            const res = await POST(req);
            expect(res.status).toBe(200);
        });
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
});

describe('Fail-closed: rotas recusam carregar sem env vars', () => {
    const ORIGINAL_ENV = { ...process.env };

    beforeEach(() => {
        jest.resetModules();
        process.env = { ...ORIGINAL_ENV };
    });

    afterAll(() => {
        process.env = ORIGINAL_ENV;
    });

    it('collect/route lança erro sem CRON_SECRET', () => {
        delete process.env.CRON_SECRET;
        delete process.env.RENDER_RUN_URL;
        expect(() => require('../app/api/cron/collect/route')).toThrow(/CRON_SECRET|RENDER_RUN_URL/);
    });

    it('digest/route lança erro sem CRON_SECRET', () => {
        delete process.env.CRON_SECRET;
        delete process.env.RENDER_DIGEST_URL;
        expect(() => require('../app/api/cron/digest/route')).toThrow(/CRON_SECRET|RENDER_DIGEST_URL/);
    });

    it('pending/route lança erro sem CRON_SECRET', () => {
        delete process.env.CRON_SECRET;
        expect(() => require('../app/api/findings/pending/route')).toThrow(/CRON_SECRET/);
    });

    it('decide/route lança erro sem CRON_SECRET', () => {
        delete process.env.CRON_SECRET;
        expect(() => require('../app/api/findings/decide/route')).toThrow(/CRON_SECRET/);
    });
});
