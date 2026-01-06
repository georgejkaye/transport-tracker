import createFetchClient from "openapi-fetch"
import createClient from "openapi-react-query"

import type { paths } from "./api"

const fetchClient = createFetchClient<paths>({
  baseUrl: "/api",
})

export const client = createClient(fetchClient)

export default client
